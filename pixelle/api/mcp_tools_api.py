# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from __future__ import annotations

from typing import Any, Dict, List, Optional
import inspect

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pixelle.mcp_core import mcp
from pixelle.manager.workflow_manager import workflow_manager


class CallToolRequest(BaseModel):
    url: Optional[str] = None  # for compatibility; ignored when calling locally
    tool: str
    args: Dict[str, Any] = {}
    headers: Optional[Dict[str, str]] = None


class ToolInfo(BaseModel):
    name: str
    description: Optional[str] = None


router = APIRouter(
    tags=["mcp-tools"],
    responses={404: {"description": "Not found"}},
)


def _dedupe_tools(tools: List[ToolInfo]) -> List[ToolInfo]:
    seen: set[str] = set()
    unique: List[ToolInfo] = []
    for t in tools:
        if t.name not in seen:
            seen.add(t.name)
            unique.append(t)
    return unique


def _get_registered_tools() -> List[ToolInfo]:
    tools: List[ToolInfo] = []

    # Try common attributes on FastMCP instance
    try:
        candidate_attrs = [
            getattr(mcp, "get_tools", None),
            getattr(mcp, "list_tools", None),
        ]
        for getter in candidate_attrs:
            if callable(getter):
                try:
                    result = getter()
                    # result may be dict, list of objects, or list of dicts
                    if isinstance(result, dict):
                        for name, val in result.items():
                            desc = getattr(val, "description", None) or (
                                val.get("description") if isinstance(val, dict) else None
                            )
                            tools.append(ToolInfo(name=name, description=desc))
                    elif isinstance(result, list):
                        for item in result:
                            name = getattr(item, "name", None) or (
                                item.get("name") if isinstance(item, dict) else None
                            )
                            if name:
                                desc = getattr(item, "description", None) or (
                                    item.get("description") if isinstance(item, dict) else None
                                )
                                tools.append(ToolInfo(name=name, description=desc))
                    if tools:
                        return _dedupe_tools(tools)
                except Exception:
                    # Continue to fallbacks
                    pass
    except Exception:
        pass

    # Fallback: workflow-based dynamic tools
    try:
        for name, info in workflow_manager.loaded_workflows.items():
            meta = info.get("metadata") or {}
            tools.append(ToolInfo(name=name, description=meta.get("description")))
    except Exception:
        pass

    # Fallback: known static tools that ship with Pixelle
    try:
        from pixelle.tools.i_crop import i_crop as i_crop_func  # type: ignore
        tools.append(ToolInfo(name="i_crop", description=(i_crop_func.__doc__ or None)))
    except Exception:
        pass

    return _dedupe_tools(tools)


def _resolve_tool_callable(tool_name: str):
    # Try FastMCP internal registry first
    try:
        for attr_name in ("_tools", "tools"):
            registry = getattr(mcp, attr_name, None)
            if isinstance(registry, dict) and tool_name in registry:
                entry = registry[tool_name]
                for candidate in ("callback", "func", "handler"):
                    func = getattr(entry, candidate, None)
                    if callable(func):
                        return func
                if callable(entry):
                    return entry
    except Exception:
        pass

    # Fallback: workflow manager
    try:
        if tool_name in workflow_manager.loaded_workflows:
            return workflow_manager.loaded_workflows[tool_name]["function"]
    except Exception:
        pass

    # Fallback: known static tools
    try:
        if tool_name == "i_crop":
            from pixelle.tools.i_crop import i_crop as i_crop_func  # type: ignore
            return i_crop_func
    except Exception:
        pass

    return None


@router.get("/")
async def list_tools(url: Optional[str] = None):  # url kept for compatibility
    print(f"list_tools: url={url}")
    tools = _get_registered_tools()
    return {"url": url, "tools": [t.model_dump() for t in tools]}


@router.post("/")
async def call_tool(payload: CallToolRequest):
    tool_name = payload.tool
    args = payload.args or {}

    func = _resolve_tool_callable(tool_name)
    if not func:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    try:
        if inspect.iscoroutinefunction(func):
            result = await func(**args)
        else:
            result = func(**args)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid arguments for tool '{tool_name}': {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool '{tool_name}' execution failed: {e}")

    return {"url": payload.url, "tool": tool_name, "args": args, "result": result}


