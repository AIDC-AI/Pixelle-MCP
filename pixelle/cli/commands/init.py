# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Reconfig command implementation."""

import typer
from rich.console import Console

from pixelle.cli.setup.execution_engines import setup_execution_engines_interactive
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
    
    # Show header information
    from pixelle.cli.utils.display import show_header_info
    show_header_info()
    
    console.print("\n🔄 [bold]Running configuration wizard...[/bold]")
    
    try:
        # Step 1: Execution engines config (ComfyUI and/or RunningHub)
        runninghub_config, comfyui_config = setup_execution_engines_interactive()
        if runninghub_config is None and comfyui_config is None:  # User cancelled
            raise KeyboardInterrupt()
        
        # Step 2: LLM config (can be configured multiple)
        llm_configs = setup_multiple_llm_providers()
        if llm_configs is None:  # User cancelled
            raise KeyboardInterrupt()
        if not llm_configs:  # Empty config
            console.print("❌ At least one LLM provider is required")
            raise typer.Exit(1)
        
        # Step 3: Select default model (based on selected providers and models)
        all_models = collect_all_selected_models(llm_configs)
        selected_default_model = select_default_model_interactively(all_models)
        if selected_default_model is None:  # User cancelled
            raise KeyboardInterrupt()

        # Step 4: Service config
        service_config = setup_service_config()
        if service_config is None:  # User cancelled
            raise KeyboardInterrupt()
        if not service_config:  # Empty config
            console.print("⚠️  Service config skipped, using default config")
            service_config = {"port": "9004", "host": "localhost"}  # Use default value
        
        # Step 5: Save config
        save_unified_config(comfyui_config, runninghub_config, llm_configs, service_config, selected_default_model)
        
        console.print("\n✅ [bold green]Configuration completed![/bold green]")
        console.print("💡 Run [bold]pixelle start[/bold] to start the server")
            
    except KeyboardInterrupt:
        console.print("\n\n❌ Configuration cancelled (Ctrl+C pressed)")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n❌ Error during configuration: {e}")
        raise typer.Exit(1)
