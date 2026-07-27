# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-Identifier: MIT).

"""Conversational workflow → MCP-tool builder.

Lets the chat LLM turn a raw ComfyUI workflow (API-format export, plain node
titles) into a registered MCP tool without forcing the user to hand-edit node
titles to the project DSL. Two modes:

- Explicit: `inspect_workflow_nodes` + `build_workflow_with_dsl` — the LLM
  emits a small mapping spec; this module rewrites node `_meta.title` strings
  to comply with `WorkflowParser`'s DSL, then delegates registration to the
  existing `WorkflowManager.load_workflow`.
- Auto: `auto_build_workflow` — infers the spec from node semantics for the
  node types we confidently know, and registers in one shot. Ambiguous or
  unknown nodes are reported as notes for the user to add explicitly.
"""

import json
import keyword
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from pixelle.comfyui.workflow_parser import WorkflowParser
from pixelle.logger import logger
from pixelle.manager.workflow_manager import workflow_manager
from pixelle.mcp_core import mcp
from pixelle.utils.file_util import download_files
from pixelle.utils.runninghub_util import is_runninghub_workflow

_PARSER = WorkflowParser()

# Param name must be a valid Python identifier (it becomes a function arg name
# via exec in WorkflowManager._generate_workflow_function) and not a keyword.
_PARAM_NAME_RE = re.compile(r"^[A-Za-z_]\w*$")
# Field name as accepted by WorkflowParser.parse_dsl_title: (\w+)
_FIELD_NAME_RE = re.compile(r"^\w+$")
_TOOL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Auto-inference rules for node types we confidently know. Only these become
# auto params; everything else is left untouched (report as a note so the user
# can add it explicitly via build_workflow_with_dsl). `~` upload marker is NOT
# set for media-load nodes because base_executor already routes them through
# `_handle_media_upload` via MEDIA_UPLOAD_NODE_TYPES.
INFERENCE_RULES: Dict[str, Dict[str, Any]] = {
    "LoadImage": {"name": "image", "field": "image", "upload": False, "description": "Input image"},
    "CLIPTextEncode": {"name": "prompt", "field": "text", "upload": False, "description": "Text prompt"},
}


class ParamSpec(BaseModel):
    """One input parameter to expose on the generated tool."""
    node_id: str = Field(description="The ComfyUI node id (as reported by inspect_workflow_nodes) whose input field becomes a tool parameter.")
    field: str = Field(description="The node's input field name to bind. Must be one of that node's settable_fields (i.e. not a node connection).")
    name: str = Field(description="The parameter name exposed by the generated MCP tool. Must be a valid identifier (letters/digits/underscore, start with letter/underscore).")
    required: bool = Field(default=True, description="Whether the parameter is required. If false, the node field must already hold a default value.")
    upload: bool = Field(default=False, description="Set true for media inputs whose value is a URL that must be downloaded and uploaded to ComfyUI before execution (e.g. a LoadImage image field).")
    description: Optional[str] = Field(default=None, description="Human-readable description of the parameter, shown to the LLM.")


class OutputSpec(BaseModel):
    """One output to return from the generated tool."""
    node_id: str = Field(description="The node id whose output should be returned by the tool.")
    var: Optional[str] = Field(default=None, description="Optional output variable name. Defaults to the node id. Use to name outputs or to mark a non-saver node as an output.")


def _is_url(source: str) -> bool:
    try:
        parsed = urlparse(source)
        return parsed.scheme in ("http", "https") and parsed.netloc
    except Exception:
        return False


def _err(msg: str) -> str:
    return json.dumps({"success": False, "error": msg})


async def _load_workflow_data(workflow_source: str) -> Dict[str, Any]:
    """Resolve a workflow source to its parsed node dict.

    Accepts an http(s) URL (downloaded to a temp file), a local file path, or a
    raw JSON string.
    """
    if _is_url(workflow_source):
        async with download_files(workflow_source) as tmp_path:
            with open(tmp_path, "r", encoding="utf-8") as f:
                return json.load(f)

    # Raw JSON string — check before the local-path stat, since a long JSON
    # string can exceed the filesystem path limit and raise on stat().
    stripped = workflow_source.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)

    # Local path
    path = Path(workflow_source)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise ValueError(
        "workflow_source must be an http(s) URL, a local file path, or a raw JSON object string."
    )


def _settable_fields(node_data: Dict[str, Any]) -> List[str]:
    """Input field names that are NOT node connections (matches
    WorkflowParser.extract_field_value: a list value is a connection)."""
    inputs = node_data.get("inputs", {})
    return [k for k, v in inputs.items() if not isinstance(v, list)]


def _reject_runninghub(workflow_source: str, data: Dict[str, Any]) -> Optional[str]:
    """Return an error string if this is a RunningHub source, else None."""
    try:
        if is_runninghub_workflow(workflow_source) or data.get("_source") == "runninghub":
            return (
                "This tool only supports standard ComfyUI workflows. "
                "For RunningHub workflows use save_workflow_tool with the workflow id instead."
            )
    except Exception:
        # is_runninghub_workflow expects a path; ignore failures for raw JSON/URL sources.
        pass
    return None


def _apply_and_register(
    data: Dict[str, Any],
    tool_name: str,
    params: List[ParamSpec],
    outputs: Optional[List[OutputSpec]],
    description: Optional[str],
) -> Any:
    """Validate the spec, rewrite node titles to DSL, and register via
    WorkflowManager. Returns the load_workflow result (dict on success,
    json error string on failure)."""
    if not isinstance(data, dict) or not data:
        return _err("Workflow is empty or not a JSON object.")

    if not re.match(_TOOL_NAME_RE, tool_name):
        return _err("tool_name is invalid: it must start with a letter/underscore and contain only letters, digits, and underscores.")
    if keyword.iskeyword(tool_name):
        return _err(f"tool_name cannot be a Python keyword: '{tool_name}'.")

    # Apply parameter DSL titles
    for spec in params:
        if not re.match(_PARAM_NAME_RE, spec.name):
            return _err(f"Parameter name '{spec.name}' is invalid: must start with a letter/underscore and contain only letters, digits, underscores.")
        if keyword.iskeyword(spec.name):
            return _err(f"Parameter name cannot be a Python keyword: '{spec.name}'.")
        if not re.match(_FIELD_NAME_RE, spec.field):
            return _err(f"Parameter '{spec.name}': field '{spec.field}' is invalid (must be \\w+).")

        node = data.get(spec.node_id)
        if not isinstance(node, dict):
            return _err(f"Parameter '{spec.name}': node id '{spec.node_id}' not found in workflow.")
        if "_meta" not in node:
            node["_meta"] = {}
        settable = _settable_fields(node)
        if spec.field not in settable:
            return _err(
                f"Parameter '{spec.name}': field '{spec.field}' is not a settable input on node '{spec.node_id}' "
                f"(it may be a node connection). Settable fields: {settable}."
            )

        title = "$" + spec.name + "." + ("~" if spec.upload else "") + spec.field
        if spec.required:
            title += "!"
        if spec.description:
            title += ":" + spec.description
        node["_meta"]["title"] = title
        logger.debug(f"build: node {spec.node_id} title -> {title}")

    # Apply output DSL titles
    if outputs:
        for spec in outputs:
            node = data.get(spec.node_id)
            if not isinstance(node, dict):
                return _err(f"Output: node id '{spec.node_id}' not found in workflow.")
            if "_meta" not in node:
                node["_meta"] = {}
            var = spec.var or str(spec.node_id)
            if not re.match(_FIELD_NAME_RE, var):
                return _err(f"Output var '{var}' is invalid (must be \\w+).")
            node["_meta"]["title"] = f"$output.{var}"
            logger.debug(f"build: node {spec.node_id} title -> $output.{var}")

    # Write modified workflow to a temp file and delegate to the existing loader.
    try:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
        try:
            return workflow_manager.load_workflow(tmp.name, tool_name=tool_name, description=description)
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"build: registration failed: {e}", exc_info=True)
        return _err(f"Failed to register workflow: {e}")


def _infer_spec(data: Dict[str, Any]) -> tuple[List[ParamSpec], int, List[str]]:
    """Infer params from known node types. Returns (params, output_node_count, notes).

    Only nodes whose class_type is in INFERENCE_RULES become params; nodes that
    already carry DSL are skipped; output saver nodes are counted (they are
    auto-detected by the parser, no title rewrite needed).
    """
    params: List[ParamSpec] = []
    used_names: set = set()
    notes: List[str] = []
    output_count = 0

    for node_id, node in data.items():
        if not isinstance(node, dict) or "_meta" not in node:
            continue
        meta = node.get("_meta") or {}
        title = meta.get("title", "") if isinstance(meta, dict) else ""
        class_type = node.get("class_type", "")
        node_id_str = str(node_id)

        # Skip nodes the user already configured with DSL.
        if _PARSER.parse_dsl_title(title) or _PARSER.parse_output_marker(title) is not None:
            continue

        if class_type in INFERENCE_RULES:
            rule = INFERENCE_RULES[class_type]
            settable = _settable_fields(node)
            if rule["field"] in settable:
                base = rule["name"]
                name = base
                i = 2
                while name in used_names:
                    name = f"{base}_{i}"
                    i += 1
                used_names.add(name)
                params.append(ParamSpec(
                    node_id=node_id_str,
                    field=rule["field"],
                    name=name,
                    required=True,
                    upload=rule["upload"],
                    description=rule["description"],
                ))
            else:
                notes.append(
                    f"node {node_id_str} ({class_type}): expected field '{rule['field']}' "
                    f"not settable (settable: {settable}); skipped."
                )

        if _PARSER.is_known_output_node(class_type):
            output_count += 1

    return params, output_count, notes


@mcp.tool(name="inspect_workflow_nodes")
async def inspect_workflow_nodes(
    workflow_source: str = Field(
        description=(
            "The ComfyUI workflow to inspect. Can be an http(s) URL to download the workflow file, "
            "a local file path, or the raw workflow JSON string (must start with '{'). "
            "Must be a standard ComfyUI API-format workflow, not a RunningHub workflow id."
        )
    ),
) -> str:
    """Inspect a raw ComfyUI workflow and list its nodes, so you can plan how to turn it into an MCP tool.

    Call this whenever the user wants to convert/add/register a ComfyUI workflow as an MCP tool but
    the workflow has not yet been given DSL node titles (i.e. it is a plain ComfyUI API-format export).
    This returns a compact node list — use it to pick which nodes should be input parameters and which
    should be outputs, then propose a mapping to the user and call build_workflow_with_dsl.

    Returns a JSON object: {"nodes": [{"node_id", "class_type", "title", "settable_fields", "is_output_node", "has_dsl"}]}.
      - settable_fields: input field names that are NOT node connections (these can become parameters).
      - is_output_node: true for known saver node types (SaveImage/SaveVideo/SaveAudio/VHS_SaveVideo/VHS_SaveAudio)
        — these are auto-detected as outputs and usually need no explicit marking.
      - has_dsl: true if the node title already follows the project DSL (so it is already a param/output marker).
    """
    try:
        data = await _load_workflow_data(workflow_source)
    except Exception as e:
        logger.error(f"inspect_workflow_nodes: failed to load source: {e}", exc_info=True)
        return _err(f"Failed to load workflow: {e}")

    if not isinstance(data, dict) or not data:
        return _err("Workflow is empty or not a JSON object.")

    nodes: List[Dict[str, Any]] = []
    for node_id, node_data in data.items():
        if not isinstance(node_data, dict) or "_meta" not in node_data:
            continue
        meta = node_data.get("_meta") or {}
        title = meta.get("title", "") if isinstance(meta, dict) else ""
        class_type = node_data.get("class_type", "")
        nodes.append({
            "node_id": str(node_id),
            "class_type": class_type,
            "title": title,
            "settable_fields": _settable_fields(node_data),
            "is_output_node": bool(_PARSER.is_known_output_node(class_type)) if class_type else False,
            "has_dsl": bool(_PARSER.parse_dsl_title(title)) or _PARSER.parse_output_marker(title) is not None,
        })

    return json.dumps({"success": True, "nodes": nodes}, ensure_ascii=False, indent=2)


@mcp.tool(name="build_workflow_with_dsl")
async def build_workflow_with_dsl(
    workflow_source: str = Field(
        description=(
            "The raw ComfyUI workflow to convert (standard API-format export, plain node titles). "
            "Can be an http(s) URL, a local file path, or raw JSON string. Must NOT be a RunningHub workflow id."
        )
    ),
    tool_name: str = Field(
        description="The MCP tool name to register. Must start with a letter/underscore and contain only letters, digits, underscores; not a Python keyword; no file extension."
    ),
    params: List[ParamSpec] = Field(
        default_factory=list,
        description="Input parameters to expose. For each, the named node's title is rewritten to the DSL so the field becomes a tool parameter. Reuses WorkflowParser DSL semantics.",
    ),
    outputs: Optional[List[OutputSpec]] = Field(
        default=None,
        description="Optional explicit outputs. Known saver nodes are auto-detected; use this to name outputs or mark non-saver nodes as outputs. Each entry sets the node title to $output.<var>.",
    ),
    description: Optional[str] = Field(
        default=None,
        description="Optional tool description / docstring shown to the LLM. Persisted across restarts via a sidecar manifest."
    ),
) -> Any:
    """Turn a raw ComfyUI workflow into a registered MCP tool by applying the project DSL automatically.

    Use this after inspect_workflow_nodes once the user has confirmed which nodes are inputs/outputs.
    This rewrites the specified node titles to the DSL form ($<name>.<field>[!][:desc] and $output.<var>)
    and registers the result as an MCP tool (reusing the existing workflow loader, so validation,
    function generation, hot-reload, and persistence all apply). The caller only provides a small
    mapping spec; it does not rewrite the whole workflow JSON.

    Common trigger phrases: "convert this workflow into a tool", "register this workflow", "make this
    workflow an MCP tool", "add this comfyui workflow".
    """
    try:
        data = await _load_workflow_data(workflow_source)
    except Exception as e:
        logger.error(f"build_workflow_with_dsl: failed to load source: {e}", exc_info=True)
        return _err(f"Failed to load workflow: {e}")

    rh_err = _reject_runninghub(workflow_source, data)
    if rh_err:
        return _err(rh_err)

    return _apply_and_register(data, tool_name, params, outputs, description)


@mcp.tool(name="auto_build_workflow")
async def auto_build_workflow(
    workflow_source: str = Field(
        description=(
            "The raw ComfyUI workflow to auto-convert (standard API-format export, plain node titles). "
            "Can be an http(s) URL, a local file path, or raw JSON string. Must NOT be a RunningHub workflow id."
        )
    ),
    tool_name: str = Field(
        description="The MCP tool name to register. Must start with a letter/underscore and contain only letters, digits, underscores; not a Python keyword; no file extension."
    ),
    description: Optional[str] = Field(
        default=None,
        description="Optional tool description / docstring shown to the LLM. If omitted, a short description is generated from the inferred inputs. Persisted across restarts via a sidecar manifest."
    ),
) -> Any:
    """Auto-convert a raw ComfyUI workflow into a registered MCP tool with zero mapping spec.

    Use this when the user just wants to throw a workflow in and have a tool generated, without
    describing each input/output. This infers parameters from node semantics for the node types it
    confidently knows (LoadImage -> image, CLIPTextEncode -> prompt, ...), leaves known saver nodes
    (SaveImage/SaveVideo/SaveAudio/...) as auto-detected outputs, and registers in one shot.

    The result includes the inferred spec and notes for anything it did NOT auto-handle (unknown node
    types, ambiguous duplicates) so the user can refine with build_workflow_with_dsl if needed.
    Nodes that already carry DSL titles are left as-is.

    Common trigger phrases: "auto generate a tool from this workflow", "一键转换", "just turn this
    workflow into a tool", "automatically add this workflow".
    """
    try:
        data = await _load_workflow_data(workflow_source)
    except Exception as e:
        logger.error(f"auto_build_workflow: failed to load source: {e}", exc_info=True)
        return _err(f"Failed to load workflow: {e}")

    rh_err = _reject_runninghub(workflow_source, data)
    if rh_err:
        return _err(rh_err)

    params, output_count, notes = _infer_spec(data)

    # Treat anything that isn't a real string (None, or an unresolved FieldInfo
    # default when called via .fn) as "not provided" and generate one.
    if not isinstance(description, str):
        param_names = ", ".join(p.name for p in params) or "none"
        description = f"Auto-generated tool '{tool_name}'. Inputs: {param_names}."

    result = _apply_and_register(data, tool_name, params, None, description)

    # Augment the result with the inferred spec + notes so the LLM/user can review.
    inferred = {
        "params": [p.model_dump() for p in params],
        "auto_detected_outputs": output_count,
        "notes": notes,
    }
    if isinstance(result, dict):
        result["inferred"] = inferred
        return result
    # result is a json error string — append inferred for context
    try:
        parsed = json.loads(result)
        parsed["inferred"] = inferred
        return json.dumps(parsed, ensure_ascii=False)
    except Exception:
        return result
