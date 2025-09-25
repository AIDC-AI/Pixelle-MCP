# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
RunningHub utility functions - centralized logic for RunningHub workflow handling
"""

import json
import os
import tempfile
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, Any

from pixelle.logger import logger
from pixelle.settings import settings
from pixelle.utils.os_util import get_data_path
from pixelle.utils.workflow_source_util import get_workflow_source, get_workflow_source_data, create_workflow_source_file


def is_runninghub_workflow(workflow_file: str | Path) -> bool:
    """Check if the workflow file is a RunningHub workflow
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        bool: True if it's a RunningHub workflow, False otherwise
    """
    return get_workflow_source(workflow_file) == "runninghub"


def get_runninghub_workflow_id(workflow_file: str | Path) -> Optional[str]:
    """Get RunningHub workflow ID from workflow file
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        Optional[str]: Workflow ID if found, None otherwise
    """
    data = get_workflow_source_data(workflow_file)
    if data and data.get("_source") == "runninghub":
        return data.get("workflow_id")
    return None


def create_runninghub_workflow_file(workflow_id: str, tool_name: str, output_dir: str = None) -> str:
    """Create a RunningHub workflow file that contains only the workflow_id
    
    Args:
        workflow_id: RunningHub workflow ID
        tool_name: Tool name for the file
        output_dir: Output directory, defaults to custom_workflows directory
        
    Returns:
        str: Path to the created workflow file
    """
    if output_dir is None:
        output_dir = get_data_path("custom_workflows")
    
    workflow_file_path = os.path.join(output_dir, f"{tool_name}.json")
    
    # Use the generic workflow source file creator
    return create_workflow_source_file(
        source="runninghub",
        source_data={"workflow_id": workflow_id},
        output_path=workflow_file_path
    )


async def validate_runninghub_workflow_id(workflow_id: str) -> bool:
    """Validate RunningHub workflow ID by checking if it exists
    
    Args:
        workflow_id: RunningHub workflow ID to validate
        
    Returns:
        bool: True if valid and exists, False otherwise
    """
    try:
        # Check if RunningHub is configured
        if not settings.runninghub_api_key:
            logger.error("RunningHub API key is not configured")
            return False
        
        # Validate workflow_id format (should be numeric)
        if not workflow_id.isdigit():
            logger.error(f"Invalid RunningHub workflow_id format: {workflow_id}. Expected numeric string.")
            return False
        
        # Test if workflow exists by trying to fetch it
        from pixelle.comfyui.runninghub_client import get_runninghub_client
        client = get_runninghub_client()
        await client.get_workflow_json(workflow_id)
        return True
    except Exception as e:
        logger.error(f"Failed to validate RunningHub workflow_id {workflow_id}: {e}")
        return False


async def fetch_runninghub_workflow_metadata(workflow_file: str | Path, tool_name: str = None):
    """Fetch and parse RunningHub workflow metadata by fetching from API
    
    Args:
        workflow_file: Path to the RunningHub workflow file
        tool_name: Optional tool name for metadata
        
    Returns:
        Optional[WorkflowMetadata]: Parsed metadata or None if failed
    """
    try:
        # Read the RunningHub workflow file using generic function
        data = get_workflow_source_data(workflow_file)
        if not data or data.get("_source") != "runninghub":
            return None
        
        workflow_id = data["workflow_id"]
        logger.info(f"Parsing RunningHub workflow metadata for workflow_id: {workflow_id}")
        
        # Get RunningHub client and fetch actual workflow
        async def fetch_and_parse():
            from pixelle.comfyui.runninghub_client import get_runninghub_client
            from pixelle.comfyui.workflow_parser import WorkflowParser
            
            client = get_runninghub_client()
            workflow_json = await client.get_workflow_json(workflow_id)
            
            # Create temporary file with the actual workflow
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(workflow_json, f, ensure_ascii=False, indent=2)
                temp_file_path = f.name
            
            try:
                # Parse using standard workflow parser
                parser = WorkflowParser()
                metadata = parser.parse_workflow_file(temp_file_path, tool_name)
                
                # Add RunningHub-specific metadata
                if metadata:
                    metadata.workflow_id = workflow_id
                    metadata.is_runninghub = True
                
                return metadata
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {temp_file_path}: {cleanup_error}")
        
        # Run the async function
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, create a new task
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, fetch_and_parse())
                return future.result()
        except RuntimeError:
            # No running loop, we can use asyncio.run
            return asyncio.run(fetch_and_parse())
            
    except Exception as e:
        logger.error(f"Failed to fetch RunningHub workflow metadata: {e}")
        return None


async def handle_runninghub_workflow_save(workflow_id: str, tool_name: str) -> Dict[str, Any]:
    """Handle RunningHub workflow by validating and saving workflow_id
    
    Args:
        workflow_id: RunningHub workflow ID
        tool_name: Tool name for the workflow
        
    Returns:
        Dict[str, Any]: Result dictionary with success status and details
    """
    try:
        # Check if RunningHub is configured
        if not settings.runninghub_api_key:
            raise Exception("RunningHub API key is not configured. Please set RUNNINGHUB_API_KEY in your environment.")
        
        # Validate workflow_id format (should be numeric)
        if not workflow_id.isdigit():
            raise Exception(f"Invalid RunningHub workflow_id format: {workflow_id}. Expected numeric string.")
        
        # Test if workflow exists by trying to fetch it
        is_valid = await validate_runninghub_workflow_id(workflow_id)
        if not is_valid:
            raise Exception(f"Failed to validate RunningHub workflow_id {workflow_id}")
        
        # Create workflow file with metadata
        workflow_file_path = create_runninghub_workflow_file(workflow_id, tool_name)
        
        return {
            "success": True,
            "workflow_file_path": workflow_file_path,
            "workflow_id": workflow_id,
            "tool_name": tool_name
        }
    
    except Exception as e:
        logger.error(f"Failed to handle RunningHub workflow {workflow_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def is_runninghub_configured() -> bool:
    """Check if RunningHub is properly configured
    
    Returns:
        bool: True if configured, False otherwise
    """
    return bool(settings.runninghub_api_key and settings.runninghub_base_url)
