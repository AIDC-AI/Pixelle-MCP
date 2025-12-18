# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re
import json

def is_valid_json_schema(obj):
    """Check if the object is a valid JSON Schema"""
    if not isinstance(obj, dict):
        return False
    
    # Must have type or be a combined schema (anyOf/oneOf/allOf)
    has_type = 'type' in obj
    has_combo = any(k in obj for k in ['anyOf', 'oneOf', 'allOf'])
    has_ref = '$ref' in obj
    
    return has_type or has_combo or has_ref or len(obj) == 0

def sanitize_value(value):
    """Clean any invalid values to ensure they are valid JSON Schema components"""
    # If it's a string, number, or boolean, return directly
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    
    # If it's a list, recursively clean each element
    if isinstance(value, list):
        # Check if all elements are strings (might be an incorrect enum or type)
        if all(isinstance(item, str) for item in value):
            # This might be a valid enum value, keep it
            return value
        # If it's a schema list (for anyOf, etc.), recursively clean
        return [sanitize_value(item) for item in value]
    
    # If it's a dictionary, recursively clean
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    
    # Convert other types to string
    return str(value)

def fix_property_schema(prop_schema: dict) -> dict:
    """Fix a single property's schema to ensure it complies with OpenAI API requirements"""
    if not isinstance(prop_schema, dict):
        return {"type": "string", "description": str(prop_schema)}
    
    fixed = {}
    
    # Standard JSON Schema fields
    VALID_FIELDS = {
        'type', 'properties', 'items', 'required', 'enum', 'description',
        'default', 'title', 'anyOf', 'oneOf', 'allOf', 'not',
        'minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'format',
        'minItems', 'maxItems', 'uniqueItems', 'additionalProperties',
        '$ref', 'const'
    }
    
    # Only keep standard fields
    for key, value in prop_schema.items():
        if key not in VALID_FIELDS:
            continue
            
        # Clean the value of each field
        if key == 'type':
            # type must be a string
            if isinstance(value, str):
                # If it contains generics or invalid characters, normalize
                if '<' in value or '>' in value or value not in ['string', 'number', 'integer', 'boolean', 'array', 'object', 'null']:
                    type_clean = re.sub(r'<[^>]+>', '', value).strip()
                    type_map = {'Map': 'object', 'List': 'array', 'String': 'string', 'Int': 'integer', 'Boolean': 'boolean', 'Any': 'string'}
                    fixed[key] = type_map.get(type_clean, 'string')
                else:
                    fixed[key] = value
            elif isinstance(value, list):
                # type is an array: take the first valid type, or treat as enum
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
            # description must be a string
            if isinstance(value, str):
                cleaned = re.sub(r'<[^>]+>', '', value).strip()
                fixed[key] = cleaned if cleaned else value
            elif value:
                fixed[key] = str(value)
                
        elif key == 'items':
            # items must be an object
            if isinstance(value, dict):
                fixed[key] = fix_property_schema(value)
            else:
                fixed[key] = {"type": "string"}
                
        elif key == 'properties':
            # properties must be an object dictionary
            if isinstance(value, dict):
                fixed[key] = {k: fix_property_schema(v) for k, v in value.items()}
                
        elif key in ['anyOf', 'oneOf', 'allOf']:
            # combined schema must be an array
            if isinstance(value, list):
                fixed[key] = [fix_property_schema(item) if isinstance(item, dict) else {"type": "string"} for item in value]
                
        elif key == 'enum':
            # enum must be an array
            if isinstance(value, list):
                fixed[key] = value
                
        else:
            # Other standard fields, keep as is but sanitize
            fixed[key] = sanitize_value(value)
    
    # Ensure there is a type or combined schema
    if 'type' not in fixed and not any(k in fixed for k in ['anyOf', 'oneOf', 'allOf', '$ref']):
        fixed['type'] = 'string'
    
    # If it's an array without items, add default items
    if fixed.get('type') == 'array' and 'items' not in fixed:
        fixed['items'] = {"type": "string"}
    
    return fixed

def tools_from_chaintlit_to_openai(chainlit_tools: list[dict]) -> dict:
    """Convert Chainlit tools to OpenAI format and fix common schema issues"""
    openai_tools = []
    
    for t in chainlit_tools:
        try:
            parameters = t.inputSchema or {}
            properties = parameters.get("properties", {})
            
            # Fix the schema for each parameter
            fixed_properties = {}
            for key, value in properties.items():
                if isinstance(value, dict):
                    fixed_properties[key] = fix_property_schema(value)
                else:
                    # If the value is not a dictionary, create a basic schema
                    fixed_properties[key] = {"type": "string", "description": str(value)}
            
            # Clean description
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
