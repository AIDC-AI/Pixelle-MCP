# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re
import json

def is_valid_json_schema(obj):
    """检查对象是否是有效的 JSON Schema"""
    if not isinstance(obj, dict):
        return False
    
    # 必须有 type 或者是组合 schema (anyOf/oneOf/allOf)
    has_type = 'type' in obj
    has_combo = any(k in obj for k in ['anyOf', 'oneOf', 'allOf'])
    has_ref = '$ref' in obj
    
    return has_type or has_combo or has_ref or len(obj) == 0

def sanitize_value(value):
    """清理任何无效的值，确保它是有效的 JSON Schema 组件"""
    # 如果是字符串或数字或布尔值，直接返回
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    
    # 如果是列表，递归清理每个元素
    if isinstance(value, list):
        # 检查是否所有元素都是字符串（可能是错误的 enum 或 type）
        if all(isinstance(item, str) for item in value):
            # 这可能是一个合法的 enum 值，保留
            return value
        # 如果是 schema 列表（用于 anyOf 等），递归清理
        return [sanitize_value(item) for item in value]
    
    # 如果是字典，递归清理
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    
    # 其他类型转为字符串
    return str(value)

def fix_property_schema(prop_schema: dict) -> dict:
    """修复单个属性的 schema，确保符合 OpenAI API 要求"""
    if not isinstance(prop_schema, dict):
        return {"type": "string", "description": str(prop_schema)}
    
    fixed = {}
    
    # 标准 JSON Schema 字段
    VALID_FIELDS = {
        'type', 'properties', 'items', 'required', 'enum', 'description',
        'default', 'title', 'anyOf', 'oneOf', 'allOf', 'not',
        'minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'format',
        'minItems', 'maxItems', 'uniqueItems', 'additionalProperties',
        '$ref', 'const'
    }
    
    # 只保留标准字段
    for key, value in prop_schema.items():
        if key not in VALID_FIELDS:
            continue
            
        # 清理每个字段的值
        if key == 'type':
            # type 必须是字符串
            if isinstance(value, str):
                # 如果包含泛型或无效字符，规范化
                if '<' in value or '>' in value or value not in ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']:
                    type_clean = re.sub(r'<[^>]+>', '', value).strip()
                    type_map = {'Map': 'object', 'List': 'array', 'String': 'string', 'Int': 'integer', 'Boolean': 'boolean', 'Any': 'string'}
                    fixed[key] = type_map.get(type_clean, 'string')
                else:
                    fixed[key] = value
            elif isinstance(value, list):
                # type 是数组：取第一个有效类型，或当作 enum
                valid_types = [t for t in value if t in ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']]
                if valid_types:
                    fixed[key] = valid_types[0]
                else:
                    fixed[key] = 'string'
                    if 'enum' not in prop_schema:
                        fixed['enum'] = value
            else:
                fixed[key] = 'string'
                
        elif key == 'description':
            # description 必须是字符串
            if isinstance(value, str):
                cleaned = re.sub(r'<[^>]+>', '', value).strip()
                fixed[key] = cleaned if cleaned else value
            elif value:
                fixed[key] = str(value)
                
        elif key == 'items':
            # items 必须是对象
            if isinstance(value, dict):
                fixed[key] = fix_property_schema(value)
            else:
                fixed[key] = {"type": "string"}
                
        elif key == 'properties':
            # properties 必须是对象字典
            if isinstance(value, dict):
                fixed[key] = {k: fix_property_schema(v) for k, v in value.items()}
                
        elif key in ['anyOf', 'oneOf', 'allOf']:
            # 组合 schema 必须是数组
            if isinstance(value, list):
                fixed[key] = [fix_property_schema(item) if isinstance(item, dict) else {"type": "string"} for item in value]
                
        elif key == 'enum':
            # enum 必须是数组
            if isinstance(value, list):
                fixed[key] = value
                
        else:
            # 其他标准字段，保持原样但清理
            fixed[key] = sanitize_value(value)
    
    # 确保有 type 或者组合 schema
    if 'type' not in fixed and not any(k in fixed for k in ['anyOf', 'oneOf', 'allOf', '$ref']):
        fixed['type'] = 'string'
    
    # 如果是数组但没有 items，添加默认 items
    if fixed.get('type') == 'array' and 'items' not in fixed:
        fixed['items'] = {"type": "string"}
    
    return fixed

def tools_from_chaintlit_to_openai(chainlit_tools: list[dict]) -> dict:
    """将 Chainlit 工具转换为 OpenAI 格式，并修复常见的 schema 问题"""
    openai_tools = []
    
    for t in chainlit_tools:
        try:
            parameters = t.inputSchema or {}
            properties = parameters.get("properties", {})
            
            # 修复每个参数的 schema
            fixed_properties = {}
            for key, value in properties.items():
                if isinstance(value, dict):
                    fixed_properties[key] = fix_property_schema(value)
                else:
                    # 如果值不是字典，创建一个基本 schema
                    fixed_properties[key] = {"type": "string", "description": str(value)}
            
            # 清理描述
            description = t.description or ""
            if isinstance(description, str):
                description = re.sub(r'<[^>]+>', '', description).strip()
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": description,
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
