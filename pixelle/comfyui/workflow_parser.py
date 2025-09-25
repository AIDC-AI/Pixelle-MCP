# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
import re
from pathlib import Path
from pixelle.logger import logger
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class WorkflowParam(BaseModel):
    name: str
    type: str = Field(default="str")
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    handler_type: Optional[str] = None

class WorkflowParamMapping(BaseModel):
    """Parameter mapping information"""
    param_name: str
    node_id: str
    input_field: str
    node_class_type: str
    handler_type: Optional[str] = None  # New: handler type

class WorkflowOutputMapping(BaseModel):
    """Output mapping information"""
    node_id: str
    output_var: str

class WorkflowMappingInfo(BaseModel):
    """Workflow mapping information"""
    param_mappings: List[WorkflowParamMapping]
    output_mappings: List[WorkflowOutputMapping]

class WorkflowMetadata(BaseModel):
    title: str
    description: Optional[str] = None
    params: Dict[str, WorkflowParam]
    mapping_info: WorkflowMappingInfo
    workflow_id: Optional[str] = None  # RunningHub workflow ID
    is_runninghub: bool = False  # Whether this is a RunningHub workflow

class WorkflowParser:
    """Workflow parser"""
    
    def __init__(self):
        pass
    
    def parse_dsl_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Parse DSL title
        
        Syntax: $<name>.[~]<field>[!][:<description>]
        where ~ means need URL upload processing, return relative path
        """
        pattern = r'^\$(\w+)\.(?:(~)?(\w+))(!)?(?::(.+))?$'
        match = re.match(pattern, title.strip())
        
        if not match:
            return None
        
        name, handler_mark, field, required_mark, description = match.groups()
        
        # Determine handler type
        handler_type = "upload_rel" if handler_mark else None
        
        return {
            'name': name,
            'field': field,
            'required': bool(required_mark),
            'description': description.strip() if description else None,
            'handler_type': handler_type
        }
    
    def infer_type_from_value(self, value: Any) -> str:
        """Infer type from value"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        else:
            return "str"
    
    def extract_field_value(self, node_data: Dict[str, Any], field_name: str) -> Any:
        """Extract value from the specified field of the node"""
        inputs = node_data.get("inputs", {})
        
        # Check if the specified field exists and is not a node connection
        if field_name in inputs and not isinstance(inputs[field_name], list):
            return inputs[field_name]
        
        return None
    
    def parse_output_marker(self, title: str) -> Optional[str]:
        """Parse output marker
        
        Format: $output.name
        """
        if not title.startswith('$output.'):
            return None
        
        output_var = title[8:]  # Remove '$output.'
        return output_var if output_var else None
    
    def is_known_output_node(self, class_type: str) -> bool:
        """Check if it is a known output node type"""
        known_output_types = {
            'SaveImage',
            'SaveVideo', 
            'SaveAudio',
            'VHS_SaveVideo',
            'VHS_SaveAudio'
        }
        return class_type in known_output_types
    
    def parse_node(self, node_id: str, node_data: Dict[str, Any]) -> tuple[Optional[WorkflowParam], Optional[WorkflowParamMapping], Optional[WorkflowOutputMapping]]:
        """Parse parameters or outputs from the node
        
        Returns:
            (param, param_mapping, output_mapping)
        """
        # Check if the node is valid
        if not isinstance(node_data, dict) or "_meta" not in node_data:
            return None, None, None
        
        title = node_data["_meta"].get("title", "")
        class_type = node_data.get("class_type", "")
        
        # 1. Check if it is an output marker
        output_var = self.parse_output_marker(title)
        if output_var:
            output_mapping = WorkflowOutputMapping(
                node_id=node_id,
                output_var=output_var
            )
            return None, None, output_mapping
        
        # 2. Check if it is a known output node
        if self.is_known_output_node(class_type):
            # Use node_id as default output variable name
            output_mapping = WorkflowOutputMapping(
                node_id=node_id,
                output_var=node_id
            )
            return None, None, output_mapping
        
        # 3. Parse DSL parameter title
        dsl_info = self.parse_dsl_title(title)
        if not dsl_info:
            return None, None, None
        
        # 4. Get field name from DSL, extract default value and infer type
        input_field = dsl_info['field']
        default_value = self.extract_field_value(node_data, input_field)
        param_type = self.infer_type_from_value(default_value) if default_value is not None else "str"
        
        # 6. Verify required logic
        is_required = dsl_info['required']
        if not is_required and default_value is None:
            message = f"Parameter `{dsl_info['name']}` has no default value but not marked as required"
            logger.error(message)
            raise Exception(message)
        
        # 7. Create parameter object
        param = WorkflowParam(
            name=dsl_info['name'],
            type=param_type,
            description=dsl_info['description'],
            required=is_required,
            default= None if is_required else default_value,
            handler_type=dsl_info['handler_type']
        )
        
        # 8. Create parameter mapping
        param_mapping = WorkflowParamMapping(
            param_name=dsl_info['name'],
            node_id=node_id,
            input_field=input_field,
            node_class_type=class_type,
            handler_type=dsl_info['handler_type']
        )
        
        return param, param_mapping, None
    
    def find_mcp_node(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find MCP node (optional)"""
        mcp_nodes = []
        for node_id, node_data in workflow_data.items():
            if (isinstance(node_data, dict) and 
                node_data.get("_meta", {}).get("title") == "MCP"):
                mcp_nodes.append(node_data)
        
        if len(mcp_nodes) == 0:
            # MCP node is optional, no error if not found
            return None
        elif len(mcp_nodes) > 1:
            logger.error(f"Workflow found multiple MCP nodes ({len(mcp_nodes)} nodes), only one MCP node is allowed")
            return None
        
        return mcp_nodes[0]
    
    def parse_mcp_node_config(self, mcp_node: Dict[str, Any]) -> Optional[str]:
        """Parse description information in MCP node"""
        try:
            inputs = mcp_node.get("inputs", {})
            
            # Find configuration fields
            possible_fields = ["value", "text", "string"]
            inputs_lower = {k.lower(): v for k, v in inputs.items()}
            
            description_content = None
            for field in possible_fields:
                if field in inputs_lower:
                    description_content = inputs_lower[field]
                    break
            
            if description_content is None:
                logger.error(f"MCP node did not find valid configuration fields, tried fields: {possible_fields}")
                return None
            
            # Directly return text content as description
            return description_content.strip() if isinstance(description_content, str) else str(description_content).strip()
            
        except Exception as e:
            logger.error(f"Parse MCP node configuration failed: {e}", exc_info=True)
            return None
    
    def parse_workflow(self, workflow_data: Dict[str, Any], title: str) -> Optional[WorkflowMetadata]:
        """Parse complete workflow"""
        # 1. Find and parse MCP node (optional)
        mcp_node = self.find_mcp_node(workflow_data)
        description = None
        
        if mcp_node:
            description = self.parse_mcp_node_config(mcp_node)
        # If there is no MCP node, description remains None, continue parsing workflow
        
        # 2. Scan all nodes, collect parameter and mapping information
        params = {}
        param_mappings = []
        output_mappings = []
        
        for node_id, node_data in workflow_data.items():
            param, param_mapping, output_mapping = self.parse_node(node_id, node_data)
            
            if param and param_mapping:
                params[param.name] = param
                param_mappings.append(param_mapping)
            
            if output_mapping:
                output_mappings.append(output_mapping)
        
        # 3. Build mapping_info
        mapping_info = WorkflowMappingInfo(
            param_mappings=param_mappings,
            output_mappings=output_mappings
        )
        
        # 4. Build metadata
        metadata = WorkflowMetadata(
            title=title,
            description=description,
            params=params,
            mapping_info=mapping_info
        )
        
        return metadata
    
    def parse_workflow_file(self, file_path: str, tool_name: Optional[str] = None) -> Optional[WorkflowMetadata]:
        """Parse workflow file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # Extract title from file name (remove suffix)
        title = tool_name or Path(file_path).stem
        
        return self.parse_workflow(workflow_data, title)
            
