/*
 Copyright (C) 2025 AIDC-AI
 This project is licensed under the MIT License (SPDX-License-identifier: MIT).
*/

// Define base service address constant
const MCP_SERVER_BASE_URL = "http://localhost:9004";
console.log("MCP_SERVER_BASE_URL", MCP_SERVER_BASE_URL);

function initMcp() {
    const mcpStorgeStr = localStorage.getItem("mcp_storage_key");
    let needInit = false;
    if (!mcpStorgeStr) {
        needInit = true;
    } else {
        try {
            const mcpStorge = JSON.parse(mcpStorgeStr);
            needInit = !mcpStorge || mcpStorge.length === 0;
            
            // Compatibility: force reinit when migrating from Docker to pixelle.ai
            if (!needInit && window.location.hostname === 'pixelle.ai') {
                const hasDockerInternalConfig = mcpStorgeStr.includes('host.docker.internal');
                if (hasDockerInternalConfig) {
                    console.log("Detected Docker internal config on pixelle.ai, forcing MCP reinit");
                    needInit = true;
                }
            }
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
            "clientType": "streamable-http",
            "command": null,
            "url": MCP_SERVER_BASE_URL + "/pixelle/mcp",
            "status": "disconnected"
        }
    ];
    localStorage.setItem("mcp_storage_key", JSON.stringify(defaultMcp));
}

initMcp();
