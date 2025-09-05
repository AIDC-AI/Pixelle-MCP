# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""OpenAI provider configuration."""

from typing import Dict, Optional
import questionary
from rich.console import Console

from pixelle.utils.network_util import get_openai_models

console = Console()


def configure_openai() -> Optional[Dict]:
    """Configure OpenAI"""
    console.print("\n🔥 [bold]Configure OpenAI compatible interface[/bold]")
    console.print("Support OpenAI official and all compatible OpenAI SDK providers")
    console.print("Including but not limited to: OpenAI, Azure OpenAI, various third-party proxy services, etc.")
    console.print("Get OpenAI official API Key: https://platform.openai.com/api-keys\n")
    
    api_key = questionary.password("Please input your OpenAI API Key:").ask()
    if not api_key:
        return None
    api_key = api_key.strip()
    
    default_base_url = "https://api.openai.com/v1"
    base_url = questionary.text(
        "OpenAI Base Url:",
        default=default_base_url,
        instruction="(press Enter to use default, or input custom base url)"
    ).ask()
    base_url = base_url.strip().rstrip('/')
    
    # Try to get model list
    console.print("🔍 Getting available model list...")
    available_models = get_openai_models(api_key, base_url)
    
    if available_models:
        console.print(f"📋 Found {len(available_models)} available models")
        
        # Important warning about function calling support
        console.print("\n⚠️  [bold yellow]Important:[/bold yellow] Please make sure to select models that support [bold]function calling[/bold]!")
        console.print("   Function calling is required for this application to work properly.")
        console.print("   Common models that support function calling include: GPT-4, GPT-4.1, etc.\n")
        
        # Create choices list with all available models
        choices = []
        for model in available_models:
            choices.append(questionary.Choice(model, model, checked=False))
        
        selected_models = questionary.checkbox(
            "Please select the model to use (space to select/cancel, enter to confirm):",
            choices=choices,
            instruction="Use arrow keys to navigate, space to select/cancel, enter to confirm"
        ).ask()
        
        if selected_models:
            models = ",".join(selected_models)
            console.print(f"✅ Selected models: {models}")
        else:
            console.print("⚠️  No models selected, using manual input")
            models = questionary.text(
                "Please input custom models:",
                instruction="(Separate multiple models with commas)"
            ).ask()
    else:
        console.print("⚠️  Cannot get model list, please input models manually")
        models = questionary.text(
            "Please input model list:",
            instruction="(multiple models separated by commas, e.g. gpt-4,gpt-3.5-turbo)"
        ).ask()
    
    return {
        "provider": "openai",
        "api_key": api_key,
        "base_url": base_url,
        "models": models
    }
