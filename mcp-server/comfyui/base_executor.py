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

from core import logger
from utils.file_util import download_files
from utils.file_uploader import upload
from comfyui.workflow_parser import WorkflowParser, WorkflowMetadata
from comfyui.models import ExecuteResult
from utils.os_util import get_data_path

# 配置变量
COMFYUI_BASE_URL = os.getenv('COMFYUI_BASE_URL')
COMFYUI_API_KEY = os.getenv('COMFYUI_API_KEY')
COMFYUI_COOKIES = os.getenv('COMFYUI_COOKIES')

# 需要特殊媒体上传处理的节点类型
MEDIA_UPLOAD_NODE_TYPES = {
    'LoadImage',
    'VHS_LoadAudioUpload', 
    'VHS_LoadVideo',
}

TEMP_DIR = get_data_path("temp")
os.makedirs(TEMP_DIR, exist_ok=True)

class ComfyUIExecutor(ABC):
    """ComfyUI 执行器抽象基类"""
    
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or COMFYUI_BASE_URL).rstrip('/')
        
    @abstractmethod
    async def execute_workflow(self, workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
        """执行工作流的抽象方法"""
        pass
    
    async def _parse_comfyui_cookies(self) -> Optional[Dict[str, str]]:
        """解析 COMFYUI_COOKIES 配置并返回 cookies 字典
        支持三种格式：
        1. HTTP URL - 发起GET请求获取cookies内容
        2. JSON字符串格式 - 直接解析
        3. 键值对字符串格式 - 解析为字典
        """
        if not COMFYUI_COOKIES:
            return None
        
        try:
            content = COMFYUI_COOKIES.strip()
            
            # 检查是否是HTTP URL
            if content.startswith(('http://', 'https://')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(content) as response:
                        if response.status != 200:
                            raise Exception(f"从URL获取cookies失败: HTTP {response.status}")
                        content = await response.text()
                        content = content.strip()
                        logger.info(f"从URL获取cookies成功: {content}")
            
            # 解析cookies内容
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
            logger.warning(f"解析COMFYUI_COOKIES失败: {e}")
            return None

    @asynccontextmanager
    async def get_comfyui_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """带cookie的aiohttp session，如果COMFYUI_COOKIES存在则自动加载"""
        cookies = await self._parse_comfyui_cookies()
        async with aiohttp.ClientSession(cookies=cookies) as session:
            yield session

    async def transfer_result_files(self, result: ExecuteResult) -> ExecuteResult:
        """转存结果文件到新的URL"""
        url_cache: Dict[str, str] = {}
        
        # 解析 ComfyUI cookies，用于下载需要认证的文件
        cookies = await self._parse_comfyui_cookies()

        def transfer_urls(urls: List[str]) -> List[str]:
            # 去重，保留顺序
            unique_urls = []
            seen = set()
            for url in urls:
                if url not in seen:
                    unique_urls.append(url)
                    seen.add(url)
            
            # 下载并上传未缓存的url
            uncached_urls = [url for url in unique_urls if url not in url_cache]
            if uncached_urls:
                with download_files(uncached_urls, cookies=cookies) as temp_files:
                    for temp_file, url in zip(temp_files, uncached_urls):
                        new_url = upload(temp_file)
                        url_cache[url] = new_url
            
            return [url_cache.get(url, url) for url in urls]

        def transfer_dict_urls(d: Dict[str, List[str]]) -> Dict[str, List[str]]:
            return {k: transfer_urls(v) for k, v in d.items()} if d else d

        # 构造新数据
        data = result.model_dump()
        for field in ["images", "audios", "videos"]:
            if data.get(field):
                data[field] = transfer_urls(data[field])
        for field in ["images_by_var", "audios_by_var", "videos_by_var"]:
            if data.get(field):
                data[field] = transfer_dict_urls(data[field])
        
        # texts是原生字符串，不需要转存
        for field in ["texts"]:
            if data.get(field):
                data[field] = data[field]
        for field in ["texts_by_var"]:
            if data.get(field):
                data[field] = data[field]
        
        return ExecuteResult(**data)

    async def _apply_param_mapping(self, workflow_data: Dict[str, Any], mapping: Any, param_value: Any):
        """根据参数映射应用单个参数"""
        node_id = mapping.node_id
        input_field = mapping.input_field
        node_class_type = mapping.node_class_type
        handler_type = getattr(mapping, 'handler_type', None)  # 获取处理类型（兼容旧版本）
        
        # 检查节点是否存在
        if node_id not in workflow_data:
            logger.warning(f"节点 {node_id} 不存在于工作流中")
            return
        
        node_data = workflow_data[node_id]
        
        # 确保inputs存在
        if "inputs" not in node_data:
            node_data["inputs"] = {}
        
        # 优先级1：检查新的DSL handler_type标记
        if handler_type == "upload_rel":
            await self._handle_media_upload(node_data, input_field, param_value)
        # 优先级2：检查节点类型是否需要特殊媒体上传处理（向后兼容）
        elif node_class_type in MEDIA_UPLOAD_NODE_TYPES:
            await self._handle_media_upload(node_data, input_field, param_value)
        else:
            # 常规参数设置
            await self._set_node_param(node_data, input_field, param_value)

    async def _handle_media_upload(self, node_data: Dict[str, Any], input_field: str, param_value: Any):
        """处理媒体上传"""
        # 确保inputs存在
        if "inputs" not in node_data:
            node_data["inputs"] = {}
        
        # 如果参数值是以http开头的URL，先上传媒体
        if isinstance(param_value, str) and param_value.startswith(('http://', 'https://')):
            try:
                # 上传媒体并获取上传后的媒体名
                media_value = await self._upload_media_from_source(param_value)
                # 使用上传后的媒体名作为节点的输入值
                await self._set_node_param(node_data, input_field, media_value)
                logger.info(f"媒体上传成功: {media_value}")
            except Exception as e:
                logger.error(f"媒体上传失败: {str(e)}")
                raise Exception(f"媒体上传失败: {str(e)}")
        else:
            # 直接使用参数值作为媒体名
            await self._set_node_param(node_data, input_field, param_value)

    async def _set_node_param(self, node_data: Dict[str, Any], input_field: str, param_value: Any):
        """设置节点参数"""
        # 确保inputs存在
        if "inputs" not in node_data:
            node_data["inputs"] = {}
        # 设置参数值
        node_data["inputs"][input_field] = param_value

    async def _upload_media_from_source(self, media_url: str) -> str:
        """从URL上传媒体"""
        async with self.get_comfyui_session() as session:
            async with session.get(media_url) as response:
                if response.status != 200:
                    raise Exception(f"下载媒体失败: HTTP {response.status}")
                
                # 从URL提取文件名
                parsed_url = urlparse(media_url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"temp_media_{hash(media_url)}.jpg"
                
                # 获取媒体数据
                media_data = await response.read()
                
                # 保存到临时文件
                suffix = os.path.splitext(filename)[1] or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_DIR) as tmp:
                    tmp.write(media_data)
                    temp_path = tmp.name
        
        try:
            # 上传临时文件到ComfyUI
            return await self._upload_media(temp_path)
        finally:
            # 删除临时文件
            os.unlink(temp_path)

    async def _upload_media(self, media_path: str) -> str:
        """上传媒体到ComfyUI"""
        # 读取媒体数据
        with open(media_path, 'rb') as f:
            media_data = f.read()
        
        # 提取文件名
        filename = os.path.basename(media_path)
        
        # 自动检测文件MIME类型
        mime_type = mimetypes.guess_type(filename)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # 准备表单数据
        data = aiohttp.FormData()
        data.add_field('image', media_data, 
                       filename=filename, 
                       content_type=mime_type)
        
        # 上传媒体
        upload_url = f"{self.base_url}/upload/image"
        async with self.get_comfyui_session() as session:
            async with session.post(upload_url, data=data) as response:
                if response.status != 200:
                    raise Exception(f"上传媒体失败: HTTP {response.status}")
                
                # 获取上传结果
                result = await response.json()
                return result.get('name', '')

    async def _apply_params_to_workflow(self, workflow_data: Dict[str, Any], metadata: WorkflowMetadata, params: Dict[str, Any]) -> Dict[str, Any]:
        """使用新解析器将参数应用到工作流"""
        workflow_data = copy.deepcopy(workflow_data)
        
        # 遍历所有参数映射
        for mapping in metadata.mapping_info.param_mappings:
            param_name = mapping.param_name
            
            # 检查参数是否存在
            if param_name in params:
                param_value = params[param_name]
                await self._apply_param_mapping(workflow_data, mapping, param_value)
            else:
                # 使用默认值（如果存在）
                if param_name in metadata.params:
                    param_info = metadata.params[param_name]
                    if param_info.default is not None:
                        await self._apply_param_mapping(workflow_data, mapping, param_info.default)
                    elif param_info.required:
                        raise Exception(f"必填参数 '{param_name}' 缺失")
        
        return workflow_data

    def _extract_output_nodes(self, metadata: WorkflowMetadata) -> Dict[str, str]:
        """从元数据提取输出节点及其输出变量名"""
        output_id_2_var = {}
        
        for output_mapping in metadata.mapping_info.output_mappings:
            output_id_2_var[output_mapping.node_id] = output_mapping.output_var
        
        return output_id_2_var

    def get_workflow_metadata(self, workflow_file: str) -> Optional[WorkflowMetadata]:
        """获取工作流元数据（使用新的解析器）"""
        parser = WorkflowParser()
        return parser.parse_workflow_file(workflow_file)

    def _split_media_by_suffix(self, node_output: Dict[str, Any], base_url: str) -> Tuple[List[str], List[str], List[str]]:
        """根据文件扩展名将媒体分为图片/视频/音频"""
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
        """根据变量名映射输出"""
        result = {}
        for node_id, media_data in output_id_2_media.items():
            # 如果有显式变量名则使用，否则使用node_id
            var_name = output_id_2_var.get(node_id, str(node_id))
            result[var_name] = media_data
        return result

    def _extend_flat_list_from_dict(self, media_dict: Dict[str, List[str]]) -> List[str]:
        """将字典中的所有列表扁平化为单个列表"""
        flat = []
        for items in media_dict.values():
            flat.extend(items)
        return flat 