# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os
import json
import copy
import tempfile
import mimetypes
from abc import ABC, abstractmethod
from urllib.parse import urlparse
from typing import Any, Optional, Dict, List, Tuple
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import aiohttp
import random

from pixelle.logger import logger
from pixelle.utils.file_util import download_files
from pixelle.utils.file_uploader import upload
from pixelle.comfyui.workflow_parser import WorkflowParser, WorkflowMetadata
from pixelle.comfyui.models import ExecuteResult
from pixelle.utils.os_util import get_data_path
from pixelle.settings import settings

# Configuration variables
COMFYUI_BASE_URL = settings.comfyui_base_url
COMFYUI_API_KEY = settings.comfyui_api_key
COMFYUI_COOKIES = settings.comfyui_cookies

# Node types that need special media upload handling
MEDIA_UPLOAD_NODE_TYPES = {
    'LoadImage',
    'VHS_LoadAudioUpload', 
    'VHS_LoadVideo',
}

TEMP_DIR = get_data_path("temp")
os.makedirs(TEMP_DIR, exist_ok=True)

class ComfyUIExecutor(ABC):
    """ComfyUI executor abstract base class"""
    
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or COMFYUI_BASE_URL).rstrip('/')
        
    @abstractmethod
    async def execute_workflow(self, workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
        """Abstract method to execute a workflow"""
        pass
    
    async def _parse_comfyui_cookies(self) -> Optional[Dict[str, str]]:
        """Parse COMFYUI_COOKIES configuration and return cookies dictionary
        Supports three formats:
        1. HTTP URL - Access cookies from a URL
        2. JSON string format - directly parse
        3. Key-value string format - parse to dictionary
        """
        if not COMFYUI_COOKIES:
            return None
        
        try:
            content = COMFYUI_COOKIES.strip()
            
            # Check if it is an HTTP URL
            if content.startswith(('http://', 'https://')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(content) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to get cookies from URL: HTTP {response.status}")
                        content = await response.text()
                        content = content.strip()
                        logger.info(f"Successfully got cookies from URL: {content}")
            
            # Parse cookies content
            if content.startswith('{'):
                return json.loads(content)
            else:
                cookies = {}
                for pair in content.split(';'):
                    if '=' in pair:
                        k, v = pair.strip().split('=', 1)
                        cookies[k.strip()] = v.strip()
                return cookies
        except Exception as e:
            logger.warning(f"Failed to parse COMFYUI_COOKIES: {e}")
            return None

    @asynccontextmanager
    async def get_comfyui_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """aiohttp session with cookies, automatically loaded if COMFYUI_COOKIES exists"""
        cookies = await self._parse_comfyui_cookies()
        async with aiohttp.ClientSession(cookies=cookies) as session:
            yield session

    async def transfer_result_files(self, result: ExecuteResult) -> ExecuteResult:
        """Transfer result files to new URLs"""
        url_cache: Dict[str, str] = {}
        
        # Parse ComfyUI cookies, for downloading files that need authentication
        cookies = await self._parse_comfyui_cookies()

        async def transfer_urls(urls: List[str]) -> List[str]:
            # Remove duplicates, preserve order
            unique_urls = []
            seen = set()
            for url in urls:
                if url not in seen:
                    unique_urls.append(url)
                    seen.add(url)
            
            # Download and upload uncached URLs
            uncached_urls = [url for url in unique_urls if url not in url_cache]
            if uncached_urls:
                async with download_files(uncached_urls, cookies=cookies) as temp_files:
                    for temp_file, url in zip(temp_files, uncached_urls):
                        new_url = upload(temp_file)
                        url_cache[url] = new_url
            
            return [url_cache.get(url, url) for url in urls]

        async def transfer_dict_urls(d: Dict[str, List[str]]) -> Dict[str, List[str]]:
            if d:
                result = {}
                for k, v in d.items():
                    result[k] = await transfer_urls(v)
                return result
            return d

        # Construct new data
        data = result.model_dump()
        for field in ["images", "audios", "videos"]:
            if data.get(field):
                data[field] = await transfer_urls(data[field])
        for field in ["images_by_var", "audios_by_var", "videos_by_var"]:
            if data.get(field):
                data[field] = await transfer_dict_urls(data[field])
        
        # texts is native string, no need to transfer
        for field in ["texts"]:
            if data.get(field):
                data[field] = data[field]
        for field in ["texts_by_var"]:
            if data.get(field):
                data[field] = data[field]
        
        return ExecuteResult(**data)

    def _generate_63bit_seed(self) -> int:
        """Generate a 63-bit random integer seed.

        Using SystemRandom to avoid global RNG side-effects in multi-threaded or
        multi-tenant environments.
        """
        return random.SystemRandom().randint(0, (1 << 63) - 1)

    def _randomize_seed_in_workflow(self, workflow_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, int]]:
        """Replace any node inputs.seed == 0 (int or string "0") with a new random seed.

        Returns a tuple of (modified_workflow, seed_changes) where seed_changes maps
        node_id (as string) to the new seed value.
        """
        changed: Dict[str, int] = {}
        for node_id, node in workflow_data.items():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs")
            if not isinstance(inputs, dict):
                continue
            if "seed" in inputs:
                val = inputs.get("seed")
                is_zero = (isinstance(val, int) and val == 0) or (isinstance(val, str) and str(val).strip() == "0")
                if is_zero:
                    new_seed = self._generate_63bit_seed()
                    inputs["seed"] = new_seed
                    changed[str(node_id)] = new_seed
        if changed:
            logger.info(f"Randomized seeds for {len(changed)} node(s): {changed}")
        return workflow_data, changed

    async def _apply_param_mapping(self, workflow_data: Dict[str, Any], mapping: Any, param_value: Any):
        """Apply single parameter based on parameter mapping"""
        node_id = mapping.node_id
        input_field = mapping.input_field
        node_class_type = mapping.node_class_type
        handler_type = getattr(mapping, 'handler_type', None)  # Get handler type (compatible with old version)
        
        # Check if node exists
        if node_id not in workflow_data:
            logger.warning(f"Node {node_id} does not exist in workflow")
            return
        
        node_data = workflow_data[node_id]
        
        # Ensure inputs exist
        if "inputs" not in node_data:
            node_data["inputs"] = {}
        
        # Priority 1: Check new DSL handler_type mark
        if handler_type == "upload_rel":
            await self._handle_media_upload(node_data, input_field, param_value)
        # Priority 2: Check if node type needs special media upload handling (backward compatibility)
        elif node_class_type in MEDIA_UPLOAD_NODE_TYPES:
            await self._handle_media_upload(node_data, input_field, param_value)
        else:
            # Regular parameter setting
            await self._set_node_param(node_data, input_field, param_value)

    async def _handle_media_upload(self, node_data: Dict[str, Any], input_field: str, param_value: Any):
        """Handle media upload"""
        # Ensure inputs exist
        if "inputs" not in node_data:
            node_data["inputs"] = {}
        
        # If parameter value is a URL starting with http, upload media first
        if isinstance(param_value, str) and param_value.startswith(('http://', 'https://')):
            try:
                # Upload media and get uploaded media name
                media_value = await self._upload_media_from_source(param_value)
                # Use uploaded media name as node input value
                await self._set_node_param(node_data, input_field, media_value)
                logger.info(f"Media upload successful: {media_value}")
            except Exception as e:
                logger.error(f"Media upload failed: {str(e)}")
                raise Exception(f"Media upload failed: {str(e)}")
        else:
            # Use parameter value as media name
            await self._set_node_param(node_data, input_field, param_value)

    async def _set_node_param(self, node_data: Dict[str, Any], input_field: str, param_value: Any):
        """Set node parameter"""
        # Ensure inputs exist
        if "inputs" not in node_data:
            node_data["inputs"] = {}
        # Set parameter value
        node_data["inputs"][input_field] = param_value

    async def _upload_media_from_source(self, media_url: str) -> str:
        """Upload media from URL"""
        async with self.get_comfyui_session() as session:
            async with session.get(media_url) as response:
                if response.status != 200:
                    raise Exception(f"Download media failed: HTTP {response.status}")
                
                # Extract filename from URL
                parsed_url = urlparse(media_url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"temp_media_{hash(media_url)}.jpg"
                
                # Get media data
                media_data = await response.read()
                
                # Save to temporary file
                suffix = os.path.splitext(filename)[1] or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_DIR) as tmp:
                    tmp.write(media_data)
                    temp_path = tmp.name
        
        try:
            # Upload temporary file to ComfyUI
            return await self._upload_media(temp_path)
        finally:
            # Delete temporary file
            os.unlink(temp_path)

    async def _upload_media(self, media_path: str) -> str:
        """Upload media to ComfyUI"""
        # Read media data
        with open(media_path, 'rb') as f:
            media_data = f.read()
        
        # Extract filename
        filename = os.path.basename(media_path)
        
        # Automatically detect file MIME type
        mime_type = mimetypes.guess_type(filename)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Prepare form data
        data = aiohttp.FormData()
        data.add_field('image', media_data, 
                       filename=filename, 
                       content_type=mime_type)
        
        # Upload media
        upload_url = f"{self.base_url}/upload/image"
        async with self.get_comfyui_session() as session:
            async with session.post(upload_url, data=data) as response:
                if response.status != 200:
                    raise Exception(f"Upload media failed: HTTP {response.status}")
                
                # Get upload result
                result = await response.json()
                return result.get('name', '')

    async def _apply_params_to_workflow(self, workflow_data: Dict[str, Any], metadata: WorkflowMetadata, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply parameters to workflow using new parser"""
        workflow_data = copy.deepcopy(workflow_data)
        
        # Iterate through all parameter mappings
        for mapping in metadata.mapping_info.param_mappings:
            param_name = mapping.param_name
            
            # Check if parameter exists
            if param_name in params:
                param_value = params[param_name]
                await self._apply_param_mapping(workflow_data, mapping, param_value)
            else:
                # Use default value (if exists)
                if param_name in metadata.params:
                    param_info = metadata.params[param_name]
                    if param_info.default is not None:
                        await self._apply_param_mapping(workflow_data, mapping, param_info.default)
                    elif param_info.required:
                        raise Exception(f"Required parameter '{param_name}' is missing")
        
        return workflow_data

    def _extract_output_nodes(self, metadata: WorkflowMetadata) -> Dict[str, str]:
        """Extract output nodes and their output variable names from metadata"""
        output_id_2_var = {}
        
        for output_mapping in metadata.mapping_info.output_mappings:
            output_id_2_var[output_mapping.node_id] = output_mapping.output_var
        
        return output_id_2_var

    def get_workflow_metadata(self, workflow_file: str) -> Optional[WorkflowMetadata]:
        """Get workflow metadata (using new parser)"""
        parser = WorkflowParser()
        return parser.parse_workflow_file(workflow_file)

    def _split_media_by_suffix(self, node_output: Dict[str, Any], base_url: str) -> Tuple[List[str], List[str], List[str]]:
        """Split media by file extension into images/videos/audios"""
        image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
        video_exts = {'.mp4', '.mov', '.avi', '.webm', '.gif'}
        audio_exts = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus'}
        
        images = []
        videos = []
        audios = []
        
        for media_key in ("images", "gifs", "audio"):
            for media_data in node_output.get(media_key, []):
                filename = media_data.get("filename")
                subfolder = media_data.get("subfolder", "")
                media_type = media_data.get("type", "output")
                
                url = f"{base_url}/view?filename={filename}"
                if subfolder:
                    url += f"&subfolder={subfolder}"
                if media_type:
                    url += f"&type={media_type}"
                
                ext = os.path.splitext(filename)[1].lower()
                if ext in image_exts:
                    images.append(url)
                elif ext in video_exts:
                    videos.append(url)
                elif ext in audio_exts:
                    audios.append(url)
        
        return images, videos, audios

    def _map_outputs_by_var(self, output_id_2_var: Dict[str, str], output_id_2_media: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Map outputs by variable name"""
        result = {}
        for node_id, media_data in output_id_2_media.items():
            # If there is an explicit variable name, use it, otherwise use node_id
            var_name = output_id_2_var.get(node_id, str(node_id))
            result[var_name] = media_data
        return result

    def _extend_flat_list_from_dict(self, media_dict: Dict[str, List[str]]) -> List[str]:
        """Flatten all lists in the dictionary into a single list"""
        flat = []
        for items in media_dict.values():
            flat.extend(items)
        return flat 