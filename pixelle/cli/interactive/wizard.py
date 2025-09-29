# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Setup wizard for interactive configuration."""

import questionary
from rich.console import Console

from pixelle.cli.setup.execution_engines import setup_execution_engines_interactive
from pixelle.cli.setup.service import setup_service_config
from pixelle.cli.setup.config_saver import save_unified_config
from pixelle.cli.setup.providers.manager import (
    setup_multiple_llm_providers,
    collect_all_selected_models,
    select_default_model_interactively
)
from pixelle.cli.utils.server_utils import start_pixelle_server

console = Console()


def run_full_setup_wizard():
    """Run full setup wizard"""
    console.print("\n🚀 [bold]Start Pixelle MCP configuration wizard[/bold]\n")
    
    try:
        # Step 1: Execution engines config (ComfyUI and/or RunningHub)
        runninghub_config, comfyui_config = setup_execution_engines_interactive()
        if runninghub_config is None and comfyui_config is None:  # User cancelled
            console.print("❌ Configuration cancelled")
            return
        
        # Step 2: LLM config (can be configured multiple)
        llm_configs = setup_multiple_llm_providers()
        if not llm_configs:
            console.print("❌ At least one LLM provider is required")
            return
        
        # Step 3: Select default model (based on selected providers and models)
        all_models = collect_all_selected_models(llm_configs)
        selected_default_model = select_default_model_interactively(all_models)

        # Step 4: Service config
        service_config = setup_service_config()
        if not service_config:
            console.print("⚠️  Service config skipped, using default config")
            service_config = {"port": "9004", "host": "localhost"}  # Use default value
        
        # Step 5: Save config
        save_unified_config(comfyui_config, runninghub_config, llm_configs, service_config, selected_default_model)
        
        # Step 6: Ask to start immediately
        console.print("\n✅ [bold green]Configuration completed![/bold green]")
        if questionary.confirm("Start Pixelle MCP immediately?", default=True, instruction="(Y/n)").ask():
            start_pixelle_server()
            
    except KeyboardInterrupt:
        console.print("\n\n❌ Configuration cancelled (Ctrl+C pressed)")

    except Exception as e:
        console.print(f"\n❌ Error during configuration: {e}")



def run_fresh_setup_wizard():
    """Reconfigure Pixelle MCP (same process as initial setup)"""
    from rich.panel import Panel
    
    console.print(Panel(
        "🔄 [bold]Initialize/reconfigure Pixelle MCP[/bold]\n\n"
        "This will start a fresh configuration process, which is the same as the initial setup.\n"
        "Existing configuration will be replaced.",
        title="Initialize/reconfigure Pixelle MCP",
        border_style="yellow"
    ))
    
    if not questionary.confirm("Are you sure you want to initialize/reconfigure Pixelle MCP?", default=True, instruction="(Y/n)").ask():
        console.print("❌ Initialization cancelled")
        return
    
    console.print("\n🚀 [bold]Start initialization wizard[/bold]\n")
    
    try:
        # Step 1: Execution engines config (ComfyUI and/or RunningHub)
        runninghub_config, comfyui_config = setup_execution_engines_interactive()
        if runninghub_config is None and comfyui_config is None:  # User cancelled
            console.print("❌ Configuration cancelled")
            return
        
        # Step 2: LLM configuration (multiple providers can be configured)
        llm_configs = setup_multiple_llm_providers()
        if not llm_configs:
            console.print("❌ At least one LLM provider is required")
            return
        
        # Step 3: Select default model (based on selected providers and models)
        all_models = collect_all_selected_models(llm_configs)
        selected_default_model = select_default_model_interactively(all_models)

        # Step 4: Service configuration
        service_config = setup_service_config()
        if not service_config:
            console.print("⚠️  Service configuration skipped, using default configuration")
            service_config = {"port": "9004", "host": "localhost"}  # Use default value
        
        # Step 5: Save configuration
        save_unified_config(comfyui_config, runninghub_config, llm_configs, service_config, selected_default_model)
        
        # Step 6: Ask if immediately start
        console.print("\n✅ [bold green]Reconfiguration completed![/bold green]")
        if questionary.confirm("Start Pixelle MCP immediately?", default=True, instruction="(Y/n)").ask():
            start_pixelle_server()
            
    except KeyboardInterrupt:
        console.print("\n\n❌ Reconfiguration cancelled (Ctrl+C pressed)")

    except Exception as e:
        console.print(f"\n❌ Error occurred during configuration: {e}")

