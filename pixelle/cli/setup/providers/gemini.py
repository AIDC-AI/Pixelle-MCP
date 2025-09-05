# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Gemini provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

console = Console()


def configure_gemini() -> Optional[Dict]:
    """Configure Gemini"""
    console.print("\n💎 [bold]Configure Google Gemini[/bold]")
    console.print("Google Gemini is the latest large language model from Google")
    console.print("Get API Key: https://makersuite.google.com/app/apikey\n")
    
    api_key = questionary.password("Please input your Gemini API Key:").ask()
    if not api_key:
        return None
    
    models = questionary.text(
        "Available models (optional):",
        default="gemini-pro,gemini-pro-vision",
        instruction="(multiple models separated by commas)"
    ).ask()
    
    return {
        "provider": "gemini",
        "api_key": api_key,
        "models": models
    }
