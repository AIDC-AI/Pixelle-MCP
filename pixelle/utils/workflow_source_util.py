# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
Workflow source utility functions - centralized logic for workflow source type detection and routing
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from pixelle.logger import logger


def get_workflow_source(workflow_file: str | Path) -> Optional[str]:
    """Get workflow source type
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        Optional[str]: Source type like 'runninghub', 'local', etc.
                      None if cannot be identified or is a standard ComfyUI workflow
    """
    try:
        if not os.path.exists(workflow_file):
            return None
            
        with open(workflow_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("_source")
    except Exception:
        return None


def is_external_workflow(workflow_file: str | Path) -> bool:
    """Check if the workflow is an external workflow (not local ComfyUI workflow)
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        bool: True if it's an external workflow that needs special handling
    """
    source = get_workflow_source(workflow_file)
    return source is not None


def has_workflow_source(workflow_file: str | Path) -> bool:
    """Check if the workflow file contains _source field
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        bool: True if contains _source field
    """
    try:
        if not os.path.exists(workflow_file):
            return False
            
        with open(workflow_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return "_source" in data
    except Exception:
        return False


def get_workflow_source_data(workflow_file: str | Path) -> Optional[Dict[str, Any]]:
    """Get complete workflow source data
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        Optional[Dict]: Dictionary containing _source and other related data,
                       None if parsing failed
    """
    try:
        if not os.path.exists(workflow_file):
            return None
            
        with open(workflow_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Only return data if it has _source field
        if "_source" not in data:
            return None
            
        return data
    except Exception as e:
        logger.error(f"Failed to parse workflow source data from {workflow_file}: {e}")
        return None


def validate_workflow_source_format(workflow_file: str | Path) -> bool:
    """Validate if the workflow source format is correct
    
    Args:
        workflow_file: Path to the workflow file
        
    Returns:
        bool: True if format is correct
    """
    try:
        data = get_workflow_source_data(workflow_file)
        if not data:
            return False
            
        # Must have _source field
        source = data.get("_source")
        if not source or not isinstance(source, str):
            return False
            
        # Source should not be empty
        if not source.strip():
            return False
            
        return True
    except Exception:
        return False


def create_workflow_source_file(source: str, source_data: Dict[str, Any], output_path: str) -> str:
    """Create a workflow file with source information
    
    Args:
        source: Source type, e.g. 'runninghub'
        source_data: Source-related data, e.g. {'workflow_id': '123456'}
        output_path: Output file path
        
    Returns:
        str: Path to the created file
    """
    # Create the workflow data with source information
    workflow_data = {
        "_source": source,
        **source_data
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the workflow file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created workflow source file: {output_path} (source: {source})")
    return output_path


def get_supported_sources() -> list[str]:
    """Get list of supported workflow source types
    
    Returns:
        list[str]: List of supported source types
    """
    return ["runninghub"]  # Will be extended as we add more sources


def is_supported_source(source: str) -> bool:
    """Check if the source type is supported
    
    Args:
        source: Source type to check
        
    Returns:
        bool: True if supported
    """
    return source in get_supported_sources()
