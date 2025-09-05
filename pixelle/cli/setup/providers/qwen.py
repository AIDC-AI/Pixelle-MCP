# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Qwen provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

console = Console()


def configure_qwen() -> Optional[Dict]:
    """Configure Qwen"""
    console.print("\n🌟 [bold]Configure Alibaba Tongyi Qwen[/bold]")
    console.print("Tongyi Qwen is a large language model developed by Alibaba")
    console.print("Get API Key: https://dashscope.console.aliyun.com/\n")
    
    api_key = questionary.password("Please input your Qwen API Key:").ask()
    if not api_key:
        return None
    
    models = questionary.text(
        "Available models (optional):",
        default="qwen-plus,qwen-turbo",
        instruction="(multiple models separated by commas)"
    ).ask()
    
    return {
        "provider": "qwen",
        "api_key": api_key, 
        "models": models
    }
