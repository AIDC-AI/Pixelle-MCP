# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""LLM provider manager."""

from typing import Dict, List, Optional
import questionary
from rich.console import Console
from rich.panel import Panel

from pixelle.cli.setup.providers.openai import configure_openai
from pixelle.cli.setup.providers.ollama import configure_ollama
from pixelle.cli.setup.providers.gemini import configure_gemini
from pixelle.cli.setup.providers.deepseek import configure_deepseek
from pixelle.cli.setup.providers.claude import configure_claude
from pixelle.cli.setup.providers.qwen import configure_qwen

console = Console()


def configure_specific_llm(provider: str) -> Optional[Dict]:
    """Configure specific LLM provider"""
    
    if provider == "openai":
        return configure_openai()
    elif provider == "ollama":
        return configure_ollama()
    elif provider == "gemini":
        return configure_gemini()
    elif provider == "deepseek":
        return configure_deepseek()
    elif provider == "claude":
        return configure_claude()
    elif provider == "qwen":
        return configure_qwen()
    
    return None


def setup_multiple_llm_providers() -> Optional[List[Dict]]:
    """Setup multiple LLM providers - Step 2"""
    console.print(Panel(
        "🤖 [bold]LLM provider configuration[/bold]\n\n"
        "Pixelle MCP supports multiple LLM providers, you can configure one or more.\n"
        "The benefits of configuring multiple providers:\n"
        "• Can use different models in different scenarios\n"
        "• Provide backup solutions, improve service availability\n"
        "• Some models perform better on specific tasks",
        title="Step 2/4: LLM provider configuration",
        border_style="green"
    ))
    
    configured_providers = []
    
    while True:
        # Show available providers
        available_providers = [
            questionary.Choice("🔥 OpenAI (recommended) - GPT-4, GPT-3.5, etc.", "openai"),
            questionary.Choice("🏠 Ollama (local) - Free local model", "ollama"),
            questionary.Choice("💎 Google Gemini - Google latest model", "gemini"),
            questionary.Choice("🚀 DeepSeek - High-performance code model", "deepseek"),
            questionary.Choice("🤖 Claude - Anthropic's powerful model", "claude"),
            questionary.Choice("🌟 Qwen - Alibaba Tongyi Qwen", "qwen"),
        ]
        
        # Filter configured providers
        remaining_providers = [p for p in available_providers 
                             if p.value not in [cp["provider"] for cp in configured_providers]]
        
        if not remaining_providers:
            console.print("✅ All available LLM providers are configured, automatically enter next step")
            break
        
        # Show currently configured providers
        if configured_providers:
            console.print("\n📋 [bold]Configured providers:[/bold]")
            for provider in configured_providers:
                console.print(f"  ✅ {provider['provider'].title()}")
        
        # Select provider to configure
        if configured_providers:
            remaining_providers.append(questionary.Choice("🏁 Complete configuration", "done"))
        
        # Always add exit option
        remaining_providers.append(questionary.Choice("❌ Cancel configuration", "cancel"))
        
        provider = questionary.select(
            "Select LLM provider to configure:" if not configured_providers else "Select LLM provider to continue configuration:",
            choices=remaining_providers
        ).ask()
        
        if provider is None:  # User pressed Ctrl+C (questionary returns None)
            return None
            
        if provider == "cancel":
            cancel_confirm = questionary.confirm("Are you sure you want to cancel configuration?", default=False, instruction="(y/N)").ask()
            if cancel_confirm is None:  # User pressed Ctrl+C during confirmation
                return None
            if cancel_confirm:
                console.print("❌ Configuration cancelled")
                return None
            else:
                continue  # Continue configuration loop
        
        if provider == "done":
            break
        
        # Configure specific provider
        provider_config = configure_specific_llm(provider)
        if provider_config:
            configured_providers.append(provider_config)
            
            # Show selected models
            models = provider_config.get('models', '')
            if models:
                model_list = [m.strip() for m in models.split(',')]
                model_display = '、'.join(model_list)
                console.print(f"✅ [bold green]{provider.title()} configuration successful![/bold green]")
                console.print(f"📋 You selected {model_display} model\n")
            else:
                console.print(f"✅ [bold green]{provider.title()} configuration successful![/bold green]\n")
        
        if not configured_providers:
            console.print("⚠️  At least one LLM provider is required to continue")
        else:
            # Check if there are any remaining providers to configure
            # remaining_providers has already filtered out configured providers, and will add "done" and "cancel" options
            actual_remaining = len([p for p in remaining_providers if p.value not in ["done", "cancel"]])
            if actual_remaining > 0:
                continue_confirm = questionary.confirm("Continue configuring other LLM providers?", default=False, instruction="(y/N)").ask()
                if continue_confirm is None:  # User pressed Ctrl+C
                    return None
                if not continue_confirm:
                    break
            else:
                # All providers are configured, automatically enter next step
                break
    
    return configured_providers


def collect_all_selected_models(llm_configs: List[Dict]) -> List[str]:
    """Collect all models from all configured providers, remove duplicates and maintain order."""
    seen = set()
    ordered_models: List[str] = []
    for conf in llm_configs or []:
        models_str = (conf.get("models") or "").strip()
        if not models_str:
            continue
        for m in models_str.split(","):
            model = m.strip()
            if model and model not in seen:
                seen.add(model)
                ordered_models.append(model)
    return ordered_models


def select_default_model_interactively(all_models: List[str]) -> Optional[str]:
    """Provide interactive selection of default model using arrow keys; return None if no models or user cancels."""
    if not all_models:
        return None

    # Default value: first item, but allow user to change
    default_choice_value = all_models[0]
    choices = [
        questionary.Choice(
            title=(m if m != default_choice_value else f"{m} (default)"),
            value=m,
            shortcut_key=None,
        )
        for m in all_models
    ]

    console.print("\n⭐ Please select the default model for the session (can be modified in .env)")
    selected = questionary.select(
        "Default model:",
        choices=choices,
        default=default_choice_value,
        instruction="Use arrow keys to navigate, press Enter to confirm",
    ).ask()

    if selected is None:  # User pressed Ctrl+C
        return None
    return selected or default_choice_value
