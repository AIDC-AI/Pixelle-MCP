# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""RunningHub configuration setup."""

from typing import Dict, Optional
import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()


def setup_runninghub() -> Optional[Dict]:
    """Setup RunningHub cloud execution engine"""
    console.print(Panel(
        "🌐 [bold]RunningHub Cloud Configuration[/bold]\n\n"
        "RunningHub provides cloud-based ComfyUI workflow execution.\n"
        "Benefits:\n"
        "• ✅ No local ComfyUI installation required\n"
        "• ✅ High-performance cloud GPUs\n"
        "• ✅ Scalable and reliable execution",
        title="RunningHub Cloud Setup",
        border_style="cyan"
    ))
    
    # Server region selection
    console.print("\n🌍 [bold]Choose RunningHub Server Region[/bold]")
    server_choice = questionary.select(
        "Which RunningHub server would you like to use?",
        choices=[
            questionary.Choice("Global (runninghub.ai) - International users", "global"),
            questionary.Choice("China (runninghub.cn) - Recommended for Chinese users", "china")
        ]
    ).ask()
    
    # Handle user cancellation (Ctrl+C)
    if server_choice is None:
        raise KeyboardInterrupt("User cancelled RunningHub server selection")
    
    # Set base URL based on selection
    if server_choice == "global":
        base_url = "https://www.runninghub.ai"
    else:  # china
        base_url = "https://www.runninghub.cn"
    
    console.print(f"✅ Selected server: {base_url}")
    
    # API Key input
    api_key = questionary.password(
        "RunningHub API Key:",
        instruction=f"(Get your API key from {base_url})"
    ).ask()
    
    # Handle user cancellation (Ctrl+C)
    if api_key is None:
        raise KeyboardInterrupt("User cancelled RunningHub API key input")
    
    if not api_key:
        console.print("⚠️  RunningHub setup skipped (no API key provided)")
        return None
    
    base_url = base_url.strip().rstrip('/')
    
    console.print(f"✅ RunningHub configured: {base_url}")
    
    return {
        "api_key": api_key,
        "base_url": base_url
    }


