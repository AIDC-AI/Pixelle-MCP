# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re
import copy

def fix_type_field(type_value):
    """修复 type 字段"""
    if isinstance(type_value, str):
        # 移除泛型标记
        if '<' in type_value or '>' in type_value:
            type_value = re.sub(r'<[^>]+>', '', type_value).strip()
        
        # 类型映射
        type_map = {
            'Map': 'object', 'HashMap': 'object', 'Dictionary': 'object',
            'List': 'array', 'ArrayList': 'array', 'Array': 'array', 'Set': 'array',
            'String': 'string', 'Int': 'integer', 'Integer': 'integer', 'Long': 'integer',
            'Float': 'number', 'Double': 'number', 'Boolean': 'boolean', 'Bool': 'boolean',
            'Any': 'string', 'Object': 'object'
        }
        
        if type_value in type_map:
            return type_map[type_value]
        elif type_value in ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']:
            return type_value
        else:
            return 'string'
    
    elif isinstance(type_value, list):
        # type 是列表，找第一个有效类型
        valid_types = ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']
        for t in type_value:
            if t in valid_types:
                return t
        return 'string'
    
    else:
        return 'string'

def fix_property_schema(schema):
    """递归修复 property schema"""
    if not isinstance(schema, dict):
        return schema
    
    # 深拷贝避免修改原始数据
    fixed = copy.deepcopy(schema)
    
    # 修复 type 字段
    if 'type' in fixed:
        fixed['type'] = fix_type_field(fixed['type'])
    
    # 修复 description 中的泛型标记
    if 'description' in fixed and isinstance(fixed['description'], str):
        fixed['description'] = re.sub(r'<[^>]+>', '', fixed['description'])
    
    # 数组必须有 items
    if fixed.get('type') == 'array' and 'items' not in fixed:
        fixed['items'] = {'type': 'string'}
    
    # 递归处理 items
    if 'items' in fixed and isinstance(fixed['items'], dict):
        fixed['items'] = fix_property_schema(fixed['items'])
    
    # 递归处理 properties
    if 'properties' in fixed and isinstance(fixed['properties'], dict):
        fixed['properties'] = {k: fix_property_schema(v) for k, v in fixed['properties'].items()}
    
    # 递归处理 anyOf/oneOf/allOf
    for key in ['anyOf', 'oneOf', 'allOf']:
        if key in fixed and isinstance(fixed[key], list):
            fixed[key] = [fix_property_schema(item) if isinstance(item, dict) else item for item in fixed[key]]
    
    return fixed

def tools_from_chaintlit_to_openai(chainlit_tools: list[dict]) -> list:
    """将 Chainlit 工具转换为 OpenAI 格式"""
    openai_tools = []
    
    for t in chainlit_tools:
        try:
            parameters = t.inputSchema or {}
            properties = parameters.get("properties", {})
            
            # 修复每个参数
            fixed_properties = {}
            for key, value in properties.items():
                fixed_properties[key] = fix_property_schema(value) if isinstance(value, dict) else value
            
            # 修复描述
            description = t.description or ""
            if isinstance(description, str):
                description = re.sub(r'<[^>]+>', '', description).strip()
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": description or "No description",
                    "parameters": {
                        "type": "object",
                        "properties": fixed_properties,
                        "required": parameters.get("required", [])
                    }
                }
            })
            
        except Exception as e:
            import logging
            logging.error(f"Failed to convert tool {getattr(t, 'name', 'unknown')}: {e}", exc_info=True)
            continue
    
    return openai_tools
