# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from typing import Dict, Any

from pixelle.comfyui.models import ExecuteResult
from pixelle.comfyui.websocket_executor import WebSocketExecutor
from pixelle.comfyui.http_executor import HttpExecutor
from pixelle.comfyui.runninghub_executor import RunningHubExecutor
from pixelle.settings import settings
from pixelle.utils.runninghub_util import is_runninghub_workflow

# Configuration variable
COMFYUI_EXECUTOR_TYPE = settings.comfyui_executor_type


class ComfyUIClient:
    """ComfyUI client Facade class, providing a unified external interface"""
    
    def __init__(self, base_url: str = None, executor_type: str = None):
        """
        Initialize ComfyUI client
        
        Args:
            base_url: ComfyUI service base URL
            executor_type: Executor type for local ComfyUI, 'websocket' or 'http'
        """
        self.base_url = base_url
        self.executor_type = executor_type or COMFYUI_EXECUTOR_TYPE
        self._executor = None
        
    def _get_executor(self):
        """Get the corresponding executor instance for local ComfyUI"""
        if self._executor is None:
            if self.executor_type == 'websocket':
                self._executor = WebSocketExecutor(self.base_url)
            elif self.executor_type == 'http':
                self._executor = HttpExecutor(self.base_url)
            else:
                raise ValueError(f"Unsupported executor type: {self.executor_type}. Valid types: 'websocket', 'http'")
        return self._executor
    
    async def execute_workflow(self, workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
        """
        Execute workflow
        
        Args:
            workflow_file: Workflow file path
            params: Workflow parameters
            
        Returns:
            Execution result
        """
        # Check if this is a RunningHub workflow by examining the file content
        if is_runninghub_workflow(workflow_file):
            # Use RunningHub executor for RunningHub workflows
            runninghub_executor = RunningHubExecutor(self.base_url)
            return await runninghub_executor.execute_workflow(workflow_file, params)
        else:
            # Use configured executor for local ComfyUI workflows
            executor = self._get_executor()
            return await executor.execute_workflow(workflow_file, params)
    
    
    def get_workflow_metadata(self, workflow_file: str):
        """
        Get workflow metadata
        
        Args:
            workflow_file: Workflow file path
            
        Returns:
            Workflow metadata
        """
        executor = self._get_executor()
        return executor.get_workflow_metadata(workflow_file)


# Create default client instance
default_client = ComfyUIClient()


# Provide convenient function interface
async def execute_workflow(workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
    """
    Convenient function to execute workflow
    
    Args:
        workflow_file: Workflow file path
        params: Workflow parameters
        
    Returns:
        Execution result
    """
    return await default_client.execute_workflow(workflow_file, params)


def get_workflow_metadata(workflow_file: str):
    """
    Convenient function to get workflow metadata
    
    Args:
        workflow_file: Workflow file path
        
    Returns:
        Workflow metadata
    """
    return default_client.get_workflow_metadata(workflow_file) 