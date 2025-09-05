# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).
from fastmcp import FastMCP

# initialize MCP server
mcp = FastMCP(
    name="pixelle-mcp-server",
    on_duplicate_tools="replace",
)
