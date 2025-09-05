# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Reconfig command implementation."""

import typer
from rich.console import Console

from pixelle.cli.setup.comfyui import setup_comfyui
from pixelle.cli.setup.service import setup_service_config
from pixelle.cli.setup.config_saver import save_unified_config
from pixelle.cli.setup.providers.manager import (
    setup_multiple_llm_providers,
    collect_all_selected_models,
    select_default_model_interactively
)

console = Console()


def init_command():
    """🔄 Initialize/reconfigure Pixelle MCP (non-interactive setup wizard)"""
    
    # Show current root path
    from pixelle.utils.os_util import get_pixelle_root_path
    current_root_path = get_pixelle_root_path()
    console.print(f"🗂️  [bold blue]Root Path:[/bold blue] {current_root_path}")
    
    console.print("🔄 [bold]Running configuration wizard...[/bold]")
    
    try:
        # Step 1: ComfyUI config
        comfyui_config = setup_comfyui()
        if not comfyui_config:
            console.print("⚠️  ComfyUI config skipped, using default config")
            comfyui_config = {"url": "http://localhost:8188"}  # Use default value
        
        # Step 2: LLM config (can be configured multiple)
        llm_configs = setup_multiple_llm_providers()
        if not llm_configs:
            console.print("❌ At least one LLM provider is required")
            raise typer.Exit(1)
        
        # Step 3: Select default model (based on selected providers and models)
        all_models = collect_all_selected_models(llm_configs)
        selected_default_model = select_default_model_interactively(all_models)

        # Step 4: Service config
        service_config = setup_service_config()
        if not service_config:
            console.print("⚠️  Service config skipped, using default config")
            service_config = {"port": "9004", "host": "localhost"}  # Use default value
        
        # Step 5: Save config
        save_unified_config(comfyui_config, llm_configs, service_config, selected_default_model)
        
        console.print("\n✅ [bold green]Configuration completed![/bold green]")
        console.print("💡 Run [bold]pixelle start[/bold] to start the server")
            
    except KeyboardInterrupt:
        console.print("\n\n❌ Configuration cancelled (Ctrl+C pressed)")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n❌ Error during configuration: {e}")
        raise typer.Exit(1)
