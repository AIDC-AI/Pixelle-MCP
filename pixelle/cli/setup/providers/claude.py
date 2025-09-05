# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Claude provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

console = Console()


def configure_claude() -> Optional[Dict]:
    """Configure Claude"""
    console.print("\n🤖 [bold]Configure Claude[/bold]")
    console.print("Claude is a powerful AI assistant developed by Anthropic")
    console.print("Get API Key: https://console.anthropic.com/\n")
    
    api_key = questionary.password("Please input your Claude API Key:").ask()
    if not api_key:
        return None
    
    models = questionary.text(
        "Available models (optional):",
        default="claude-3-sonnet-20240229,claude-3-haiku-20240307",
        instruction="(multiple models separated by commas)"
    ).ask()
    
    return {
        "provider": "claude",
        "api_key": api_key,
        "models": models
    }
