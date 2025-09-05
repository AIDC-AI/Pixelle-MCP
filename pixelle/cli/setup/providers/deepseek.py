# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""DeepSeek provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

console = Console()


def configure_deepseek() -> Optional[Dict]:
    """Configure DeepSeek"""
    console.print("\n🚀 [bold]Configure DeepSeek[/bold]")
    console.print("DeepSeek is a highly cost-effective code-specific model")
    console.print("Get API Key: https://platform.deepseek.com/api_keys\n")
    
    api_key = questionary.password("Please input your DeepSeek API Key:").ask()
    if not api_key:
        return None
    
    models = questionary.text(
        "Available models (optional):",
        default="deepseek-chat,deepseek-coder",
        instruction="(multiple models separated by commas)"
    ).ask()
    
    return {
        "provider": "deepseek",
        "api_key": api_key,
        "models": models
    }
