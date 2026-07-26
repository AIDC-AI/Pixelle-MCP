# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pixelle MCP — an AIGC agent framework that converts ComfyUI workflows into MCP tools with zero code. A single unified FastAPI app simultaneously hosts: (1) an MCP server (FastMCP) for external MCP clients like Cursor/Claude Desktop, (2) a Chainlit-based chat web UI that runs an LLM-in-the-loop calling those MCP tools, and (3) a file service. It supports two execution backends — local ComfyUI and cloud ComfyUI via RunningHub — selected per-workflow at runtime.

The central idea is **Workflow-as-MCP-Tool**: a ComfyUI workflow JSON (exported in *API format*) is parsed for a small DSL embedded in node titles, a Python handler function is generated and `exec`'d at runtime, and registered as an MCP tool that can be hot-added/removed without restarting.

## Commands

```bash
# Local development (run from the project root, which becomes the "Pixelle root path")
uv run pixelle            # interactive mode (default) — guides config wizard then starts
uv run pixelle start      # start service directly (foreground)
uv run pixelle start -d   # daemon/background
uv run pixelle start -f   # force-start (kills conflicting processes on the port)
uv run pixelle stop        # stop all pixelle processes
uv run pixelle status      # service/port/config status
uv run pixelle logs -f     # follow logs
uv run pixelle workflow    # list loaded workflows / MCP tools
uv run pixelle init        # (re)run config wizard
uv run pixelle dev         # debug/system info

# One-off without install
uvx pixelle@latest

# Docker
docker compose up --build   # serves on :9004, mounts ./data and ./.env

# Direct module run during development
uv run python -m pixelle.main      # runs uvicorn on settings.host:settings.port
```

No test framework is configured; there are no tests. The web UI runs at `http://localhost:9004`; the MCP endpoint clients connect to is `http://localhost:9004/mcp` (also mounted at `/pixelle`). Default port `9004` (override via `PORT`).

## Configuration

All config is environment-variable based via pydantic-settings (`pixelle/settings.py`); copy `.env.example` to `.env` in the project root (the CWD at launch). Key groups: service (`HOST`/`PORT`/`PUBLIC_READ_URL`), ComfyUI (`COMFYUI_BASE_URL`, `COMFYUI_API_KEY`, `COMFYUI_COOKIES`, `COMFYUI_EXECUTOR_TYPE`=http|websocket), RunningHub (`RUNNINGHUB_BASE_URL`, `RUNNINGHUB_API_KEY`), Chainlit auth, CDN strategy (`CDN_STRATEGY`=auto|china|global), and LLM providers (OpenAI/Ollama/Gemini/DeepSeek/Claude/Qwen — each with `*_BASE_URL`/`*_API_KEY`/`*_MODELS`; models are comma-separated). `settings.py` **must be imported before any other pixelle module** — it loads `.env` and sets Chainlit env vars on import.

## Architecture

### Unified app assembly (`pixelle/main.py`)

A single FastAPI `app` is built by composing three pieces:
1. `mcp.http_app(path='/mcp')` — the FastMCP ASGI app, mounted at `/pixelle`.
2. Chainlit's own FastAPI app: its routes are copied into this app (standard OpenAPI/doc paths skipped to avoid conflicts) and its middleware transferred. Chainlit's entry file `pixelle/web/app.py` is loaded via `load_module`.
3. `files_api` router at `/files`.

The two lifespans (MCP + Chainlit) are nested in `combined_lifespan`. Three custom middlewares sit in front: `HTMLCDNReplaceMiddleware` (rewrites jsdelivr/Google Fonts CDN prefixes for China access), `AppJsMiddleware` (serves fresh `app.js` in dev), `StaticCacheMiddleware` (proper HTTP caching for hashed assets). OpenAPI generation is overridden by `openapi_util.create_custom_openapi_function`.

### The MCP server (`pixelle/mcp_core.py`)

A single `FastMCP(name="pixelle-mcp-server", on_duplicate_tools="replace")` instance. `on_duplicate_tools="replace"` is what lets workflows be hot-updated. Tools come from two sources:
- **Built-in tools** imported manually in `main.py`: `pixelle.tools.i_crop` and `pixelle.tools.workflow_manager_tool` (which exposes `save_workflow_tool`, `reload_workflows_tool`, `list_workflows_tool`, `get_workflow_tool_detail`, `remove_workflow_tool` — these are how the LLM/user adds workflows at runtime).
- **Dynamic workflow tools** registered by `WorkflowManager`.

### Workflow → MCP tool pipeline (`pixelle/manager/workflow_manager.py` + `pixelle/comfyui/workflow_parser.py`)

`WorkflowManager` (singleton `workflow_manager`, auto-runs `load_all_workflows()` on import) scans `data/custom_workflows/*.json` and, for each file:
1. **Parse metadata** — `WorkflowParser` reads the ComfyUI API-format JSON. Node titles carry a DSL:
   - **Parameter**: `$<param_name>.[~]<field>[!][:description>]`. `~` marks `handler_type="upload_rel"` (download URL → upload to ComfyUI → use relative path). `!` = required. `field` is the node input to inject into. Type is inferred from the field's current value (bool/int/float/str). A node whose target field is already a list (a connection) is skipped.
   - **Output**: `$output.var_name` marks a node whose output becomes a tool return value. Otherwise known saver node types (`SaveImage`, `SaveVideo`, `SaveAudio`, `VHS_SaveVideo`, `VHS_SaveAudio`) are auto-detected as outputs keyed by node id.
   - **Description**: a node titled `MCP` (with a `value`/`text`/`string` input) provides the tool's docstring/description.
2. **Generate handler** — `_generate_workflow_function` builds an `async def <title>(<params>)` source string (required params first, optional with defaults via `Field(...)`), then `exec()`s it with `execute_workflow` and `WORKFLOW_PATH` injected into its globals.
3. **Register** — `mcp.tool(handler)` registers it; metadata + load time recorded in `loaded_workflows`. The workflow file is copied into `CUSTOM_WORKFLOW_DIR` if not already there.

`unload_workflow`/`reload_all_workflows` call `mcp.remove_tool()` and delete/clear files. The tool name must match `^[a-zA-Z0-9_\.-]+$` (workflow path) / `^[A-Za-z_][A-Za-z0-9_]*$` (non-Python-keyword, enforced by `save_workflow_tool`).

### ComfyUI execution (`pixelle/comfyui/`)

`ComfyUIClient` (facade) decides the backend per call: `is_runninghub_workflow(workflow_file)` checks for a `_source: "runninghub"` marker in the file → `RunningHubExecutor`; otherwise the configured local executor (`HttpExecutor` or `WebSocketExecutor`, selected by `COMFYUI_EXECUTOR_TYPE`). `WorkflowManager.parse_workflow_metadata` fetches real workflow JSON from RunningHub's API for RunningHub files (uses a thread-pool `asyncio.run` bridge when already inside an event loop).

`ComfyUIExecutor` (base) does the heavy lifting shared by local executors:
- `_apply_params_to_workflow` deep-copies the workflow and, for each `param_mapping`, injects the value into `node.inputs[field]`. Media params (`handler_type=="upload_rel"` or known `LoadImage`/`VHS_*` node types) trigger `_handle_media_upload`: if the value is an HTTP URL it's downloaded and uploaded to ComfyUI's `/upload/image`, returning the server-side name.
- `_randomize_seed_in_workflow` replaces any `inputs.seed == 0` with a fresh 63-bit `SystemRandom` seed (so `seed=0` means "randomize").
- Outputs are collected from the known saver nodes / `$output.var` markers, split by file extension into images/videos/audios, and `transfer_result_files` re-hosts them via the local `upload()` so URLs are stable/public.
- `ExecuteResult.to_llm_result()` formats a compact string for the LLM (e.g. `Generated successfully, images: [...]`).

### Chat / LLM-in-the-loop (`pixelle/web/`)

Chainlit entry: `web/app.py`. `on_chat_start` seeds a system prompt (file → settings → `DEFAULT_SYSTEM_PROMPT`) and chat settings. `on_mcp_connect` lists the in-process MCP tools and converts them to OpenAI tool schema (`tool_converter`). `on_message` (→ `chat_handler.process_streaming_response`) is the agentic loop:
- Builds OpenAI-format messages from the Chainlit context (`message_converter`), uploads any attached media to get URLs.
- Calls `litellm.accompletion(..., stream=True, tools=<mcp tools as openai schema>, tool_choice="auto")` with `model=f"{provider}/{model}"`.
- Streams tokens; accumulates `tool_calls` deltas. On `finish_reason=="tool_calls"`, executes each call via the Chainlit MCP session (`mcp_session.call_tool`, 1h read timeout), appends `role:"tool"` results, and loops.
- `_extract_and_clean_media_markers` scans LLM output for `[SHOW_IMAGE:...]` / `[SHOW_AUDIO:...]` / `[SHOW_VIDEO:...]` markers and attaches them as inline Chainlit elements (URL or local path).

LLM providers are surfaced as Chainlit "chat profiles" (`web/utils/llm_util.get_all_models`), one per configured model. Errors are normalized by `format_llm_error_message`.

### Path model (`pixelle/utils/os_util.py`)

The **current working directory at launch is the Pixelle root path** (not the package dir). Layout under it: `data/custom_workflows/` (workflow tools), `data/custom_starters/`, `files/` (uploaded/generated media), `temp/`. Package source (`SRC_PATH` = `pixelle/`) holds the bundled `.chainlit/`, `public/`, and example `workflows/` repo-root `workflows/*.json` are the samples to copy into `data/custom_workflows/`. `.env` is read from the root path. In Docker, `WORKDIR /app` with `./data` volume-mounted.

## Conventions

- Every source file starts with the copyright/MIT header comment.
- `from pixelle.settings import settings` is imported first in `main.py` (and `mcp_core`/`settings` before tools) — env must load before anything reads config.
- Dynamic tool functions are generated as source strings and `exec`'d — when changing the template in `_generate_workflow_function`, keep the `exec` globals dict (`execute_workflow`, `WORKFLOW_PATH`, `logger`, `Field`, `metadata`) in sync with what the template references.
- Workflows must be exported from ComfyUI in **API format**, not UI format.
