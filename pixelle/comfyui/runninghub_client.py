# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
import tempfile
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path
import aiohttp
import asyncio

from pixelle.logger import logger
from pixelle.settings import settings


class RunningHubClient:
    """RunningHub API client for workflow and file operations"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.runninghub_api_key
        self.base_url = (base_url or settings.runninghub_base_url).rstrip('/')
        self.timeout = settings.runninghub_timeout
        self.retry_count = settings.runninghub_retry_count
        
        if not self.api_key:
            raise ValueError("RunningHub API key is required")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          files: Optional[Dict] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Make HTTP request to RunningHub API with retry logic"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        # Prepare request data
        if files:
            # For file upload, don't set Content-Type (let aiohttp handle it)
            request_data = aiohttp.FormData()
            if data:
                for key, value in data.items():
                    request_data.add_field(key, str(value))
            for key, file_info in files.items():
                request_data.add_field(key, file_info['content'], filename=file_info['filename'])
        else:
            # For JSON requests
            headers['Content-Type'] = 'application/json'
            request_data = json.dumps(data) if data else None
        
        # Retry logic
        last_exception = None
        for attempt in range(self.retry_count + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout or self.timeout)) as session:
                    async with session.request(method, url, headers=headers, data=request_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('code') == 0:
                                return result
                            else:
                                raise Exception(f"RunningHub API error: {result.get('msg', 'Unknown error')}")
                        else:
                            response_text = await response.text()
                            raise Exception(f"HTTP {response.status}: {response_text}")
                            
            except Exception as e:
                last_exception = e
                if attempt < self.retry_count:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.retry_count + 1} attempts: {e}")
        
        raise last_exception
    
    async def get_workflow_json(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow JSON by workflow ID using getJsonApiFormat API
        
        Args:
            workflow_id: RunningHub workflow ID
            
        Returns:
            Workflow JSON data
        """
        logger.info(f"Getting workflow JSON for workflow_id: {workflow_id}")
        
        data = {
            "apiKey": self.api_key,
            "workflowId": workflow_id
        }
        
        try:
            result = await self._make_request("POST", "/api/openapi/getJsonApiFormat", data=data)
            prompt_str = result.get('data', {}).get('prompt', '')
            
            if not prompt_str:
                raise Exception("No workflow JSON found in response")
            
            # Parse the JSON string to get the actual workflow object
            import json
            workflow_json = json.loads(prompt_str)
            
            logger.info(f"Successfully retrieved workflow JSON for {workflow_id}")
            return workflow_json
            
        except Exception as e:
            logger.error(f"Failed to get workflow JSON for {workflow_id}: {e}")
            raise
    
    async def save_workflow_to_temp_file(self, workflow_id: str) -> str:
        """Get workflow JSON and save to temporary file
        
        Args:
            workflow_id: RunningHub workflow ID
            
        Returns:
            Path to temporary workflow file
        """
        workflow_json = await self.get_workflow_json(workflow_id)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(workflow_json, f, ensure_ascii=False, indent=2)
            temp_file_path = f.name
        
        logger.info(f"Workflow saved to temporary file: {temp_file_path}")
        return temp_file_path
    
    async def upload_file(self, file_path: str) -> str:
        """Upload file to RunningHub
        
        Args:
            file_path: Local file path to upload
            
        Returns:
            RunningHub fileName (as required by LoadImage nodes)
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Uploading file to RunningHub: {file_path}")
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        filename = Path(file_path).name
        
        data = {
            "apiKey": self.api_key
        }
        
        files = {
            "file": {
                "content": file_content,
                "filename": filename
            }
        }
        
        try:
            result = await self._make_request("POST", "/task/openapi/upload", data=data, files=files)
            upload_data = result.get('data', {})
            
            # According to RunningHub documentation, the response should contain fileName
            file_name = upload_data.get('fileName', '')
            
            if not file_name:
                # Fallback to URL if fileName is not available
                file_url = upload_data.get('url', '')
                if file_url:
                    logger.warning(f"fileName not found in response, using URL: {file_url}")
                    return file_url
                else:
                    raise Exception("Neither fileName nor URL found in upload response")
            
            logger.info(f"File uploaded successfully, fileName: {file_name}")
            return file_name
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    async def create_task(self, workflow_id: str, node_info_list: List[Dict] = None) -> Dict[str, Any]:
        """Create workflow execution task
        
        Args:
            workflow_id: RunningHub workflow ID
            node_info_list: Node parameter modifications
            
        Returns:
            Task creation result
        """
        logger.info(f"Creating task for workflow_id: {workflow_id}")
        
        data = {
            "apiKey": self.api_key,
            "workflowId": workflow_id
        }
        
        if node_info_list:
            data["nodeInfoList"] = node_info_list
        
        try:
            result = await self._make_request("POST", "/task/openapi/create", data=data)
            task_data = result.get('data', {})
            
            logger.info(f"Task created successfully: {task_data.get('taskId')}")
            return task_data
            
        except Exception as e:
            logger.error(f"Failed to create task for {workflow_id}: {e}")
            raise
    
    async def query_task_status(self, task_id: str) -> Literal["QUEUED", "RUNNING", "FAILED", "SUCCESS"]:
        """Query task execution status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status string: one of "QUEUED", "RUNNING", "FAILED", "SUCCESS"
        """
        data = {
            "apiKey": self.api_key,
            "taskId": task_id
        }
        
        try:
            result = await self._make_request("POST", "/task/openapi/status", data=data)
            # According to RunningHub API docs, the data field is a string: ["QUEUED","RUNNING","FAILED","SUCCESS"]
            return result.get('data', 'FAILED')
            
        except Exception as e:
            logger.error(f"Failed to query task status for {task_id}: {e}")
            raise
    
    async def query_task_result(self, task_id: str) -> List[Dict[str, Any]]:
        """Query task execution result
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result information
        """
        data = {
            "apiKey": self.api_key,
            "taskId": task_id
        }
        
        try:
            result = await self._make_request("POST", "/task/openapi/outputs", data=data)
            return result.get('data', [])
            
        except Exception as e:
            logger.error(f"Failed to query task result for {task_id}: {e}")
            raise


# Global RunningHub client instance
_runninghub_client = None

def get_runninghub_client() -> RunningHubClient:
    """Get global RunningHub client instance"""
    global _runninghub_client
    if _runninghub_client is None:
        _runninghub_client = RunningHubClient()
    return _runninghub_client
