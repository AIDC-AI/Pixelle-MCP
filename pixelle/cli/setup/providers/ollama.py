# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Ollama provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

from pixelle.utils.network_util import test_ollama_connection, get_ollama_models

console = Console()


def configure_ollama() -> Optional[Dict]:
    """Configure Ollama"""
    console.print("\n🏠 [bold]Configure Ollama (local model)[/bold]")
    console.print("Ollama can run open-source models locally, completely free and data does not leave the machine")
    console.print("Install Ollama: https://ollama.ai\n")
    
    default_base_url = "http://localhost:11434/v1"
    base_url = questionary.text(
        "Ollama address:",
        default=default_base_url,
        instruction="(press Enter to use default, or input custom address)"
    ).ask()
    
    # Test connection
    console.print("🔌 Testing Ollama connection...")
    if test_ollama_connection(base_url):
        console.print("✅ Ollama connection successful")
        
        # Get available models
        models = get_ollama_models(base_url)
        if models:
            console.print(f"📋 Found {len(models)} available models")
            selected_models = questionary.checkbox(
                "Please select the model to use:",
                choices=[questionary.Choice(model, model) for model in models]
            ).ask()
            
            if selected_models:
                return {
                    "provider": "ollama", 
                    "base_url": base_url,
                    "models": ",".join(selected_models)
                }
        else:
            console.print("⚠️  No available models found, you may need to download models first")
            console.print("e.g. ollama pull llama2")
            
            models = questionary.text(
                "Please manually specify models:",
                instruction="(multiple models separated by commas)"
            ).ask()
            
            if models:
                return {
                    "provider": "ollama",
                    "base_url": base_url, 
                    "models": models
                }
    else:
        console.print("❌ Cannot connect to Ollama")
        console.print("Please ensure Ollama is running")
        
    return None
