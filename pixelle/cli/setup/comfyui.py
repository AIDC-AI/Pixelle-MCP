# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""ComfyUI configuration setup."""

from typing import Dict, Optional
import questionary
from rich.console import Console
from rich.panel import Panel



console = Console()


def setup_comfyui(default_url: str = None) -> Optional[Dict]:
    """Setup ComfyUI - Step 1"""
    console.print(Panel(
        "🧩 [bold]ComfyUI configuration[/bold]\n\n"
        "Pixelle MCP needs to connect to your ComfyUI service to execute workflows.\n"
        "ComfyUI is a powerful AI workflow editor, if you haven't installed it yet,\n"
        "please visit: https://github.com/comfyanonymous/ComfyUI",
        title="Step 1/4: ComfyUI configuration",
        border_style="blue"
    ))
    
    # Manual config
    console.print("\n📝 Please configure ComfyUI service address")
    
    # Direct text input with default value
    final_default_url = default_url or "http://localhost:8188"
    url = questionary.text(
        "ComfyUI address:",
        default=final_default_url,
        instruction="(press Enter to use default, or input custom address)"
    ).ask()
    
    # Handle user cancellation (Ctrl+C)
    if url is None:
        raise KeyboardInterrupt("User cancelled ComfyUI address input")
    
    if not url:  # User entered empty string
        return None
    url = url.strip().rstrip('/')
    
    console.print(f"✅ ComfyUI address set to: {url}")
    
    # API Key Configuration
    api_key = questionary.password(
        "ComfyUI API Key (optional, for ComfyUI API Nodes):",
        instruction="(Leave empty if not using API Nodes)"
    ).ask()
    
    # Handle user cancellation (Ctrl+C)
    if api_key is None:
        raise KeyboardInterrupt("User cancelled ComfyUI API key input")
    
    config = {"url": url}
    if api_key:
        config["api_key"] = api_key
        console.print("✅ ComfyUI API Key configured")
    
    return config
