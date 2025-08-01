/*
 Copyright (C) 2025 AIDC-AI
 This project is licensed under the MIT License (SPDX-License-identifier: MIT).
*/

// 定义基础服务地址常量
const MCP_SERVER_BASE_URL = "http://localhost:9002";

function initMcp() {
    const mcpStorgeStr = localStorage.getItem("mcp_storage_key");
    let needInit = false;
    if (!mcpStorgeStr) {
        needInit = true;
    } else {
        try {
            const mcpStorge = JSON.parse(mcpStorgeStr);
            needInit = !mcpStorge || mcpStorge.length === 0;
        } catch (error) {
            needInit = true;
        }
    }
    if (!needInit) {
        return;
    }

    const defaultMcp = [
        {
            "name": "pixelle-mcp", 
            "tools": [],
            "clientType": "sse",
            "command": null,
            "url": MCP_SERVER_BASE_URL + "/sse",
            "status": "disconnected"
        }
    ];
    localStorage.setItem("mcp_storage_key", JSON.stringify(defaultMcp));
}

initMcp();
