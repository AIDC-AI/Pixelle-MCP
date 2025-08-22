# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
import re
from pathlib import Path
from core import logger
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class WorkflowParam(BaseModel):
    name: str
    type: str = Field(default="str")
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    handler_type: Optional[str] = None  # 新增：处理类型，如 "upload_rel" 表示URL上传返回相对路径

class WorkflowParamMapping(BaseModel):
    """参数映射信息"""
    param_name: str
    node_id: str
    input_field: str
    node_class_type: str
    handler_type: Optional[str] = None  # 新增：处理类型

class WorkflowOutputMapping(BaseModel):
    """输出映射信息"""
    node_id: str
    output_var: str

class WorkflowMappingInfo(BaseModel):
    """工作流映射信息"""
    param_mappings: List[WorkflowParamMapping]
    output_mappings: List[WorkflowOutputMapping]

class WorkflowMetadata(BaseModel):
    title: str
    description: Optional[str] = None
    params: Dict[str, WorkflowParam]
    mapping_info: WorkflowMappingInfo

class WorkflowParser:
    """工作流解析器"""
    
    def __init__(self):
        pass
    
    def parse_dsl_title(self, title: str) -> Optional[Dict[str, Any]]:
        """解析DSL标题
        
        语法: $<name>.[~]<field>[!][:<description>]
        其中 ~ 表示需要URL上传处理，返回相对路径
        """
        pattern = r'^\$(\w+)\.(?:(~)?(\w+))(!)?(?::(.+))?$'
        match = re.match(pattern, title.strip())
        
        if not match:
            return None
        
        name, handler_mark, field, required_mark, description = match.groups()
        
        # 确定处理类型
        handler_type = "upload_rel" if handler_mark else None
        
        return {
            'name': name,
            'field': field,
            'required': bool(required_mark),
            'description': description.strip() if description else None,
            'handler_type': handler_type
        }
    
    def infer_type_from_value(self, value: Any) -> str:
        """从值推断类型"""
        if isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "bool"
        else:
            return "str"
    
    def extract_field_value(self, node_data: Dict[str, Any], field_name: str) -> Any:
        """从节点的指定字段提取值"""
        inputs = node_data.get("inputs", {})
        
        # 检查指定字段是否存在且不是节点连接
        if field_name in inputs and not isinstance(inputs[field_name], list):
            return inputs[field_name]
        
        return None
    
    def parse_output_marker(self, title: str) -> Optional[str]:
        """解析输出标记
        
        格式: $output.name
        """
        if not title.startswith('$output.'):
            return None
        
        output_var = title[8:]  # 移除'$output.'
        return output_var if output_var else None
    
    def is_known_output_node(self, class_type: str) -> bool:
        """检查是否是已知的输出节点类型"""
        known_output_types = {
            'SaveImage',
            'SaveVideo', 
            'SaveAudio',
            'VHS_SaveVideo',
            'VHS_SaveAudio'
        }
        return class_type in known_output_types
    
    def parse_node(self, node_id: str, node_data: Dict[str, Any]) -> tuple[Optional[WorkflowParam], Optional[WorkflowParamMapping], Optional[WorkflowOutputMapping]]:
        """从节点解析参数或输出
        
        Returns:
            (param, param_mapping, output_mapping)
        """
        # 检查节点是否有效
        if not isinstance(node_data, dict) or "_meta" not in node_data:
            return None, None, None
        
        title = node_data["_meta"].get("title", "")
        class_type = node_data.get("class_type", "")
        
        # 1. 检查是否是输出标记
        output_var = self.parse_output_marker(title)
        if output_var:
            output_mapping = WorkflowOutputMapping(
                node_id=node_id,
                output_var=output_var
            )
            return None, None, output_mapping
        
        # 2. 检查是否是已知输出节点
        if self.is_known_output_node(class_type):
            # 使用node_id作为默认输出变量名
            output_mapping = WorkflowOutputMapping(
                node_id=node_id,
                output_var=node_id
            )
            return None, None, output_mapping
        
        # 3. 解析DSL参数标题
        dsl_info = self.parse_dsl_title(title)
        if not dsl_info:
            return None, None, None
        
        # 4. 从DSL获取字段名，提取默认值并推断类型
        input_field = dsl_info['field']
        default_value = self.extract_field_value(node_data, input_field)
        param_type = self.infer_type_from_value(default_value) if default_value is not None else "str"
        
        # 6. 验证required逻辑
        is_required = dsl_info['required']
        if not is_required and default_value is None:
            message = f"Parameter `{dsl_info['name']}` has no default value but not marked as required"
            logger.error(message)
            raise Exception(message)
        
        # 7. 创建参数对象
        param = WorkflowParam(
            name=dsl_info['name'],
            type=param_type,
            description=dsl_info['description'],
            required=is_required,
            default= None if is_required else default_value,
            handler_type=dsl_info['handler_type']
        )
        
        # 8. 创建参数映射
        param_mapping = WorkflowParamMapping(
            param_name=dsl_info['name'],
            node_id=node_id,
            input_field=input_field,
            node_class_type=class_type,
            handler_type=dsl_info['handler_type']
        )
        
        return param, param_mapping, None
    
    def find_mcp_node(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找MCP节点（可选）"""
        mcp_nodes = []
        for node_id, node_data in workflow_data.items():
            if (isinstance(node_data, dict) and 
                node_data.get("_meta", {}).get("title") == "MCP"):
                mcp_nodes.append(node_data)
        
        if len(mcp_nodes) == 0:
            # MCP节点是可选的，没有找到时不报错
            return None
        elif len(mcp_nodes) > 1:
            logger.error(f"工作流中发现多个MCP节点({len(mcp_nodes)}个)，只允许存在一个MCP节点")
            return None
        
        return mcp_nodes[0]
    
    def parse_mcp_node_config(self, mcp_node: Dict[str, Any]) -> Optional[str]:
        """解析MCP节点中的description信息"""
        try:
            inputs = mcp_node.get("inputs", {})
            
            # 查找配置字段
            possible_fields = ["value", "text", "string"]
            inputs_lower = {k.lower(): v for k, v in inputs.items()}
            
            description_content = None
            for field in possible_fields:
                if field in inputs_lower:
                    description_content = inputs_lower[field]
                    break
            
            if description_content is None:
                logger.error(f"MCP节点中未找到有效的配置字段，尝试的字段: {possible_fields}")
                return None
            
            # 直接返回文本内容作为description
            return description_content.strip() if isinstance(description_content, str) else str(description_content).strip()
            
        except Exception as e:
            logger.error(f"解析MCP节点配置失败: {e}", exc_info=True)
            return None
    
    def parse_workflow(self, workflow_data: Dict[str, Any], title: str) -> Optional[WorkflowMetadata]:
        """解析完整工作流"""
        # 1. 查找并解析MCP节点（可选）
        mcp_node = self.find_mcp_node(workflow_data)
        description = None
        
        if mcp_node:
            description = self.parse_mcp_node_config(mcp_node)
        # 如果没有MCP节点，description保持为None，继续解析工作流
        
        # 2. 扫描所有节点，收集参数和映射信息
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
        
        # 3. 构建mapping_info
        mapping_info = WorkflowMappingInfo(
            param_mappings=param_mappings,
            output_mappings=output_mappings
        )
        
        # 4. 构建metadata
        metadata = WorkflowMetadata(
            title=title,
            description=description,
            params=params,
            mapping_info=mapping_info
        )
        
        return metadata
    
    def parse_workflow_file(self, file_path: str, tool_name: Optional[str] = None) -> Optional[WorkflowMetadata]:
        """解析工作流文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # 从文件名提取title（移除后缀）
        title = tool_name or Path(file_path).stem
        
        return self.parse_workflow(workflow_data, title)
            
