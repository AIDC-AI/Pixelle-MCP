# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

def tools_from_chaintlit_to_openai(chainlit_tools: list[dict]) -> dict:
    openai_tools = []
    for t in chainlit_tools:
        parameters = t.inputSchema
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters["properties"],
                    "required": parameters.get("required", [])
                }
            }
        })
    return openai_tools
