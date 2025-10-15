# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os
import json
import time
import uuid
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse
import websockets

from pixelle.comfyui.base_executor import ComfyUIExecutor, COMFYUI_API_KEY, logger
from pixelle.comfyui.models import ExecuteResult


class WebSocketExecutor(ComfyUIExecutor):
    """WebSocket executor for ComfyUI"""
    
    def __init__(self, base_url: str = None):
        super().__init__(base_url)
        self._parse_ws_url()
        
        logger.info(f"HTTP Base URL: {self.http_base_url}")
        logger.info(f"WebSocket Base URL: {self.ws_base_url}")
    
    def _parse_ws_url(self):
        """Parse API URL and build WebSocket URL"""
        # Use standard URL parser to parse base_url
        parsed = urlparse(self.base_url)
        
        # Determine WebSocket scheme based on original scheme
        ws_scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        http_scheme = 'https' if parsed.scheme == 'https' else 'http'
        
        # Original path
        base_path = parsed.path.rstrip('/')

        # Build WebSocket URL, add /ws path
        ws_netloc = parsed.netloc
        ws_path = f"{base_path}/ws"
        self.ws_base_url = urlunparse((ws_scheme, ws_netloc, ws_path, '', '', ''))
        
        # Build HTTP URL, keep original structure
        self.http_base_url = urlunparse((http_scheme, ws_netloc, base_path, '', '', ''))

    async def _queue_prompt(self, workflow: Dict[str, Any], client_id: str, prompt_ext_params: Optional[Dict[str, Any]] = None) -> str:
        """Submit workflow to queue"""
        prompt_data = {
            "prompt": workflow,
            "client_id": client_id
        }
        
        # Update all parameters of prompt_data and prompt_ext_params
        if prompt_ext_params:
            prompt_data.update(prompt_ext_params)
        
        json_data = json.dumps(prompt_data)
        
        # Use aiohttp to send request
        prompt_url = f"{self.base_url}/prompt"
        async with self.get_comfyui_session() as session:
            async with session.post(
                    prompt_url, 
                    data=json_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"Submit workflow failed: [{response.status}] {response_text}")
                
                result = await response.json()
                prompt_id = result.get("prompt_id")
                if not prompt_id:
                    raise Exception(f"Get prompt_id failed: {result}")
                logger.info(f"Task submitted: {prompt_id}")
                return prompt_id

    def _parse_ws_message(self, message: dict, prompt_id: str) -> tuple[bool, dict]:
        """
        Parse websocket message
        
        Args:
            message: websocket message
            prompt_id: prompt_id to listen
            
        Returns:
            (invoke completed, message content)
        """
        invoke_completed = False
        if message.get('type') == 'executing':
            data = message.get('data', {})
            if data.get('node') is None and data.get('prompt_id') == prompt_id:
                invoke_completed = True
        return invoke_completed, message

    def _build_result_from_collected_outputs(self, collected_outputs: Dict[str, Any], prompt_id: str, output_id_2_var: Optional[Dict[str, str]] = None) -> ExecuteResult:
        """
        Build execution result from collected WebSocket outputs
        """
        try:
            logger.info(f"Build execution result from collected WebSocket outputs (prompt_id: {prompt_id})")
            
            # Collect all images, videos, audios and texts outputs by file extension
            output_id_2_images = {}
            output_id_2_videos = {}
            output_id_2_audios = {}
            output_id_2_texts = {}
            
            for node_id, output in collected_outputs.items():
                images, videos, audios = self._split_media_by_suffix(output, self.http_base_url)
                if images:
                    output_id_2_images[node_id] = images
                if videos:
                    output_id_2_videos[node_id] = videos
                if audios:
                    output_id_2_audios[node_id] = audios
                
                # Collect text outputs
                if "text" in output:
                    texts = output["text"]
                    if isinstance(texts, str):
                        texts = [texts]
                    elif not isinstance(texts, list):
                        texts = [str(texts)]
                    output_id_2_texts[node_id] = texts
            
            result = ExecuteResult(
                status="completed",
                prompt_id=prompt_id,
                outputs=collected_outputs
            )
            
            # If there is a mapping, map by variable name
            if output_id_2_images:
                result.images_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_images)
                result.images = self._extend_flat_list_from_dict(result.images_by_var)

            if output_id_2_videos:
                result.videos_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_videos)
                result.videos = self._extend_flat_list_from_dict(result.videos_by_var)

            if output_id_2_audios:
                result.audios_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_audios)
                result.audios = self._extend_flat_list_from_dict(result.audios_by_var)

            # Process texts/texts_by_var
            if output_id_2_texts:
                result.texts_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_texts)
                result.texts = self._extend_flat_list_from_dict(result.texts_by_var)
            
            if not (result.images or result.videos or result.audios or result.texts):
                logger.warning("No outputs found")
                result.status = "error"
                result.msg = "No outputs found"
            
            logger.info(f"Build result successfully, output count: images={len(result.images)}, videos={len(result.videos)}, audios={len(result.audios)}, texts={len(result.texts)}")
            
            return result
        except Exception as e:
            logger.error(f"Build execution result from collected WebSocket outputs failed: {str(e)}")
            return ExecuteResult(
                status="error",
                prompt_id=prompt_id,
                msg=f"Build execution result from collected WebSocket outputs failed: {str(e)}"
            )

    async def execute_workflow(self, workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
        """Execute workflow (WebSocket way)"""
        try:
            start_time = time.time()
            
            if not os.path.exists(workflow_file):
                logger.error(f"Workflow file does not exist: {workflow_file}")
                return ExecuteResult(status="error", msg=f"Workflow file does not exist: {workflow_file}")
            
            # Get workflow metadata
            metadata = self.get_workflow_metadata(workflow_file)
            if not metadata:
                return ExecuteResult(status="error", msg="Cannot parse workflow metadata")
            
            # Load workflow JSON
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            if not workflow_data:
                return ExecuteResult(status="error", msg="Workflow data is missing")
            
            # Use new parameter mapping logic
            if params:
                workflow_data = await self._apply_params_to_workflow(workflow_data, metadata, params)
            else:
                # Even if no parameters are passed, default values need to be applied
                workflow_data = await self._apply_params_to_workflow(workflow_data, metadata, {})

            # Replace any seed == 0 with a random 63-bit seed before submission
            workflow_data, _ = self._randomize_seed_in_workflow(workflow_data)
            
            # Extract output node information from metadata
            output_id_2_var = self._extract_output_nodes(metadata)
            
            # Generate client ID
            client_id = str(uuid.uuid4())
            
            # Prepare extra parameters
            prompt_ext_params = {}
            if COMFYUI_API_KEY:
                prompt_ext_params = {
                    "extra_data": {
                        "api_key_comfy_org": COMFYUI_API_KEY
                    }
                }
            else:
                logger.warning("COMFYUI_API_KEY is not set")
            
            # First establish WebSocket connection, then submit task
            timeout = 30 * 60  # Default 30 minutes timeout
            
            # Build WebSocket URL
            ws_url = f"{self.ws_base_url}?clientId={client_id}"
            logger.info(f"WebSocket URL: {ws_url}")
            logger.info(f"Prepare to connect websocket service")
            
            # For collecting nodes with outputs
            collected_outputs = {}
            prompt_id = None
            
            try:
                # Prepare extra headers for WebSocket connection, include cookies
                additional_headers = {}
                cookies = await self._parse_comfyui_cookies()
                if cookies:
                    try:
                        if isinstance(cookies, dict):
                            cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                        else:
                            cookie_string = str(cookies)
                        
                        additional_headers["Cookie"] = cookie_string
                        logger.debug(f"WebSocket connection will use cookies: {cookie_string[:50]}...")
                    except Exception as e:
                        logger.warning(f"Parse WebSocket cookies failed: {e}")
                
                # Establish WebSocket connection
                async with websockets.connect(ws_url, additional_headers=additional_headers) as websocket:
                    logger.info('WebSocket connection established, now submit workflow')
                    
                    # After connection established, immediately submit workflow
                    try:
                        prompt_id = await self._queue_prompt(workflow_data, client_id, prompt_ext_params)
                    except Exception as e:
                        error_message = f"Submit workflow failed: [{type(e)}] {str(e)}"
                        logger.error(error_message)
                        return ExecuteResult(status="error", msg=error_message)
                    
                    logger.info(f"Workflow submitted, prompt_id: {prompt_id}, now wait for result")
                    
                    while True:
                        # Check timeout
                        elapsed = time.time() - start_time
                        if elapsed > timeout:
                            logger.warning(f"WebSocket timeout ({timeout} seconds)")
                            result = ExecuteResult(
                                status="timeout",
                                prompt_id=prompt_id,
                                msg=f"WebSocket timeout ({timeout} seconds)",
                                duration=elapsed
                            )
                            return result
                        
                        try:
                            # Wait for message, set shorter timeout to check total timeout
                            message_str = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            
                            if not isinstance(message_str, str):
                                continue
                                
                            message = json.loads(message_str)
                            
                            # Print full message for target prompt_id for debugging
                            if message.get('data', {}).get('prompt_id') == prompt_id:
                                logger.debug(f'Received target WebSocket message (prompt_id: {prompt_id}): {json.dumps(message, ensure_ascii=False)}')
                                
                                # Process different types of messages
                                msg_type = message.get('type')
                                data = message.get('data', {})
                                
                                if msg_type == 'execution_cached':
                                    # Process cached execution message
                                    cached_nodes = data.get('nodes', [])
                                    logger.debug(f"Detected cached execution, skip nodes: {cached_nodes}")
                                    
                                elif msg_type == 'executed':
                                    # Collect nodes with outputs
                                    node_id = data.get('node')
                                    output = data.get('output')
                                    if output and node_id:
                                        # Check if there are outputs we are interested in
                                        has_media = output.get('images') \
                                            or output.get('gifs') \
                                            or output.get('audio') \
                                            or output.get('text')
                                        if has_media:
                                            logger.info(f"Collected outputs from node {node_id}")
                                            collected_outputs[node_id] = output
                                            
                                elif msg_type == 'execution_error':
                                    # Process execution error
                                    error_message = data.get('exception_message', 'Unknown error')
                                    logger.error(f"Execution error: {error_message}")
                                    return ExecuteResult(
                                        status="error",
                                        prompt_id=prompt_id,
                                        msg=error_message,
                                        duration=time.time() - start_time
                                    )
                            else:
                                # For status message, record queue status
                                if message.get('type') == 'status':
                                    queue_remaining = message.get('data', {}).get('status', {}).get('exec_info', {}).get('queue_remaining', 'unknown')
                                    logger.debug(f'Queue status updated: remaining tasks {queue_remaining} ')
                                else:
                                    logger.debug(f'Received other WebSocket message: {message}')
                            
                            # Parse message
                            invoke_completed, parsed_message = self._parse_ws_message(message, prompt_id)
                            
                            if invoke_completed:
                                logger.info('WebSocket detected execution completed')
                                
                                # Set execution duration
                                duration = time.time() - start_time
                                
                                # If there are collected outputs, use them to build result
                                if collected_outputs:
                                    result = self._build_result_from_collected_outputs(collected_outputs, prompt_id, output_id_2_var)
                                    result.duration = duration
                                    # Transfer result files
                                    result = await self.transfer_result_files(result)
                                    return result
                                else:
                                    # WebSocket way did not collect any outputs, return error
                                    logger.warning("WebSocket did not collect any outputs")
                                    result = ExecuteResult(
                                        status="error",
                                        prompt_id=prompt_id,
                                        msg="WebSocket did not collect any outputs",
                                        duration=duration
                                    )
                                    return result
                                
                        except asyncio.TimeoutError:
                            # Wait for message timeout, continue loop to check total timeout
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            result = ExecuteResult(
                                status="error",
                                prompt_id=prompt_id,
                                msg="WebSocket connection closed",
                                duration=time.time() - start_time
                            )
                            return result
                            
            except Exception as e:
                logger.error(f"WebSocket connection or execution exception: {str(e)}")
                result = ExecuteResult(
                    status="error",
                    prompt_id=prompt_id,
                    msg=f"WebSocket connection or execution exception: {str(e)}",
                    duration=time.time() - start_time
                )
                return result
                
        except Exception as e:
            logger.error(f"Execute workflow failed: {str(e)}", exc_info=True)
            return ExecuteResult(status="error", msg=str(e)) 