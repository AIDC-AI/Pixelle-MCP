# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Ollama provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

from pixelle.utils.network_util import test_ollama_connection, get_ollama_models, test_lmstudio_connection, get_lmstudio_models

console = Console()


def configure_lmstudio() -> Optional[Dict]:
    """Configure LM Studio"""
    console.print("\n🏠 [bold]Configure LM Studio (local model)[/bold]")
    console.print("LM Studio can run open-source models locally, completely free and data does not leave the machine")
    console.print("Install LM Studio: https://lmstudio.ai/\n")
    
    default_base_url = "http://localhost:1234/v1"
    base_url = questionary.text(
        "LM Studio address:",
        default=default_base_url,
        instruction="(press Enter to use default, or input custom address)"
    ).ask()
    
    # Test connection
    console.print("🔌 Testing LM Studio connection...")
    if test_lmstudio_connection(base_url):
        console.print("✅ LM Studio connection successful")
        
        # Get available models
        models = get_lmstudio_models(base_url)
        if models:
            console.print(f"📋 Found {len(models)} available models")
            selected_models = questionary.checkbox(
                "Please select the model to use:",
                choices=[questionary.Choice(model, model) for model in models]
            ).ask()
            
            if selected_models:
                return {
                    "provider": "lmstudio",
                    "base_url": base_url,
                    "models": ",".join(selected_models)
                }
        else:
            console.print("⚠️  No available models found, you may need to download models first")
            console.print(" see LM Studio documentation for how to add models\n")
            
            models = questionary.text(
                "Please manually specify models:",
                instruction="(multiple models separated by commas)"
            ).ask()
            
            if models:
                return {
                    "provider": "lmstudio",
                    "base_url": base_url, 
                    "models": models
                }
    else:
        console.print("❌ Cannot connect to LM Studio")
        console.print("Please ensure LM Studio is running")
        
    return None
