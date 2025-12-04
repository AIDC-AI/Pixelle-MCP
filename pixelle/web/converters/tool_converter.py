# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re

def normalize_type_value(type_value: str) -> str:
    """规范化类型值，将编程语言类型转换为 JSON Schema 类型"""
    if not isinstance(type_value, str):
        return type_value
    
    # 移除泛型标记和尖括号内容 (如 Map<String, Any> -> Map)
    type_value = re.sub(r'<[^>]+>', '', type_value).strip()
    
    # 类型映射表
    type_mapping = {
        'Map': 'object',
        'HashMap': 'object',
        'Dictionary': 'object',
        'List': 'array',
        'ArrayList': 'array',
        'Array': 'array',
        'Set': 'array',
        'String': 'string',
        'Int': 'integer',
        'Integer': 'integer',
        'Long': 'integer',
        'Float': 'number',
        'Double': 'number',
        'Boolean': 'boolean',
        'Bool': 'boolean',
        'Any': 'string',  # 默认为 string
        'Object': 'object',
    }
    
    return type_mapping.get(type_value, 'string')

def clean_description(description: str) -> str:
    """清理描述中的无效内容"""
    if not isinstance(description, str):
        return description
    
    # 移除类型标记如 Map<String, Any>
    cleaned = re.sub(r'Map<[^>]+>', 'object', description)
    cleaned = re.sub(r'List<[^>]+>', 'array', cleaned)
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    
    return cleaned.strip()

def fix_property_schema(prop_schema: dict) -> dict:
    """修复单个属性的 schema"""
    if not isinstance(prop_schema, dict):
        return prop_schema
    
    fixed = prop_schema.copy()
    
    # 1. 修复 type 字段
    if "type" in fixed:
        prop_type = fixed["type"]
        
        # 如果 type 是列表（无效格式），尝试修复
        if isinstance(prop_type, list):
            # 可能是错误地将 enum 放在了 type 字段
            # 或者是包含多个类型，取第一个有效类型
            if all(isinstance(t, str) for t in prop_type):
                # 如果看起来像 enum 值，将其移到 enum 字段
                valid_types = ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']
                type_candidates = [t for t in prop_type if t in valid_types]
                
                if type_candidates:
                    # 找到有效的 JSON Schema 类型
                    fixed["type"] = type_candidates[0]
                else:
                    # 都不是有效类型，可能是 enum 值，移到 enum 字段
                    fixed["type"] = "string"
                    if "enum" not in fixed:
                        fixed["enum"] = prop_type
            else:
                # 无法识别的格式，默认为 string
                fixed["type"] = "string"
        
        elif isinstance(prop_type, str):
            # 检查是否包含无效的类型定义
            if '<' in prop_type or '>' in prop_type or prop_type not in ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']:
                fixed["type"] = normalize_type_value(prop_type)
        
        else:
            # type 字段不是字符串也不是列表，使用默认值
            fixed["type"] = "string"
    
    # 2. 修复 description 字段
    if "description" in fixed and isinstance(fixed["description"], str):
        fixed["description"] = clean_description(fixed["description"])
    
    # 3. 如果是数组类型但缺少 items，添加默认的 items
    if fixed.get("type") == "array" and "items" not in fixed:
        fixed["items"] = {"type": "string"}
    
    # 4. 递归处理嵌套的 items (数组元素)
    if "items" in fixed and isinstance(fixed["items"], dict):
        fixed["items"] = fix_property_schema(fixed["items"])
    
    # 5. 递归处理嵌套的 properties (对象属性)
    if "properties" in fixed and isinstance(fixed["properties"], dict):
        fixed["properties"] = fix_schema_properties(fixed["properties"])
    
    # 6. 递归处理组合 schema (anyOf, oneOf, allOf)
    for combo_key in ['anyOf', 'oneOf', 'allOf']:
        if combo_key in fixed and isinstance(fixed[combo_key], list):
            fixed[combo_key] = [
                fix_property_schema(item) if isinstance(item, dict) else item
                for item in fixed[combo_key]
            ]
    
    # 注意：不再删除任何字段，保持原始 schema 结构
    # 只修复明确有问题的字段（type, items, description 等）
    # 让 OpenAI API 自己处理不认识的字段
    
    return fixed

def fix_schema_properties(properties: dict) -> dict:
    """修复所有属性的 schema"""
    if not isinstance(properties, dict):
        return properties
    
    fixed_properties = {}
    for key, value in properties.items():
        if isinstance(value, dict):
            fixed_properties[key] = fix_property_schema(value)
        else:
            fixed_properties[key] = value
    
    return fixed_properties

def tools_from_chaintlit_to_openai(chainlit_tools: list[dict]) -> dict:
    """将 Chainlit 工具转换为 OpenAI 格式，并修复常见的 schema 问题"""
    import logging
    openai_tools = []
    
    for t in chainlit_tools:
        try:
            parameters = t.inputSchema
            
            # 修复参数 schema（包括类型规范化、数组 items、嵌套对象等）
            fixed_properties = fix_schema_properties(parameters.get("properties", {}))
            
            # 清理工具描述
            tool_description = t.description
            if isinstance(tool_description, str):
                tool_description = clean_description(tool_description)
            
            tool_def = {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": fixed_properties,
                        "required": parameters.get("required", [])
                    }
                }
            }
            
            # 调试：输出第一个工具的 schema
            if t.name == "get_github_clones":
                logging.info(f"Tool {t.name} properties: {fixed_properties}")
            
            openai_tools.append(tool_def)
            
        except Exception as e:
            # 如果某个工具转换失败，记录错误但继续处理其他工具
            logging.error(f"Failed to convert tool {getattr(t, 'name', 'unknown')}: {e}", exc_info=True)
            continue
    
    return openai_tools
