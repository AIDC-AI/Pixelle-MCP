# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Development command implementation."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

console = Console()


def dev_command():
    """🔧 Display development and debugging information"""
    
    # Show header information
    from pixelle.cli.utils.display import show_header_info
    show_header_info()
    
    # Get current root path for directory information
    from pixelle.utils.os_util import get_pixelle_root_path
    current_root_path = get_pixelle_root_path()
    
    # Check configuration status first
    from pixelle.cli.utils.command_utils import detect_config_status
    config_status = detect_config_status()
    
    if config_status == "first_time":
        console.print("❌ [bold red]No configuration found![/bold red]")

        raise typer.Exit(1)
    elif config_status == "incomplete":
        console.print("❌ [bold red]Configuration is incomplete![/bold red]")

        raise typer.Exit(1)
    
    # Core Directory Information
    dir_table = Table(title="📁 Core Directories", show_header=True, header_style="bold cyan")
    dir_table.add_column("Directory", style="cyan", width=25)
    dir_table.add_column("Path", style="yellow", width=50)
    dir_table.add_column("Status", width=15)
    
    try:
        from pixelle.utils.os_util import get_data_path, get_src_path
        
        directories = [
            ("Project Root", current_root_path),
            ("Source Code", get_src_path()),
            ("Data Directory", get_data_path()),
            ("Custom Workflows", get_data_path("custom_workflows")),
            ("Configuration", Path(current_root_path) / ".env"),
        ]
        
        for dir_name, dir_path in directories:
            path_obj = Path(dir_path)
            if path_obj.exists():
                if path_obj.is_file():
                    status = "✅ File"
                else:
                    status = "✅ Directory"
            else:
                status = "❌ Missing"
            
            dir_table.add_row(dir_name, str(dir_path), status)
        
        console.print(dir_table)
        
    except Exception as e:
        console.print(f"📁 [yellow]Directory information unavailable: {e}[/yellow]")
    
    # Environment Variables (.env file content)
    console.print("\n🔧 [bold].env Configuration:[/bold]")
    
    try:
        env_path = Path(current_root_path) / ".env"
        if env_path.exists():
            env_vars = []  # Use list to preserve order
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars.append((key.strip(), value.strip().strip('"\'')))
            
            if env_vars:
                env_tree = Tree(".env Configuration")
                for key, value in env_vars:  # Keep original order from .env file
                    # Handle sensitive values with better visibility for debugging
                    if 'API_KEY' in key.upper() or 'SECRET' in key.upper():
                        if not value:
                            masked_value = "[red]Not set[/red]"
                        else:
                            # Show first 4 and last 4 characters for debugging
                            if len(value) > 8:
                                masked_value = f"[green]{value[:4]}***{value[-4:]}[/green]"
                            else:
                                masked_value = "[green]***configured***[/green]"
                    else:
                        masked_value = value if value else "[red]Empty[/red]"
                    env_tree.add(f"[cyan]{key}[/cyan] = {masked_value}")
                console.print(env_tree)
            else:
                console.print("  [yellow].env file is empty[/yellow]")
        else:
            console.print("  [yellow].env file does not exist[/yellow]")
    
    except Exception as e:
        console.print(f"  [yellow].env information unavailable: {e}[/yellow]")
    
    # Service Status Check (from status command)
    console.print("\n🌐 [bold]Service Status:[/bold]")
    
    try:
        # Reload config to ensure we have latest settings
        from pixelle.cli.setup.config_saver import reload_config
        reload_config()
        
        from pixelle.settings import settings
        from pixelle.utils.network_util import check_url_status, check_mcp_streamable, test_comfyui_connection
        
        # Create status table
        status_table = Table(title="Service Status", show_header=True, header_style="bold blue")
        status_table.add_column("Service", style="cyan", width=20)
        status_table.add_column("Address", style="yellow", width=40)
        status_table.add_column("Status", width=15)
        status_table.add_column("Description", style="white")
        
        # Check services
        pixelle_url = f"http://{settings.host}:{settings.port}"
        pixelle_mcp_server_url = f"{pixelle_url}/pixelle/mcp"
        
        # Check MCP endpoint
        mcp_status = check_mcp_streamable(pixelle_mcp_server_url)
        status_table.add_row(
            "MCP endpoint",
            pixelle_mcp_server_url,
            "🟢 Available" if mcp_status else "🔴 Unavailable",
            "MCP protocol endpoint" if mcp_status else "Please start the service first"
        )
        
        # Check Web interface
        web_status = check_url_status(pixelle_url)
        status_table.add_row(
            "Web interface",
            pixelle_url,
            "🟢 Available" if web_status else "🔴 Unavailable",
            "Chat interface" if web_status else "Please start the service first"
        )
        
        # Check ComfyUI
        comfyui_status = test_comfyui_connection(settings.comfyui_base_url)
        status_table.add_row(
            "ComfyUI",
            settings.comfyui_base_url,
            "🟢 Connected" if comfyui_status else "🔴 Connection failed",
            "Workflow execution engine" if comfyui_status else "Please check if ComfyUI is running"
        )
        
        console.print(status_table)
        
        # Service Summary
        total_services = 3  # MCP, Web, ComfyUI
        running_services = sum([mcp_status, web_status, comfyui_status])
        
        if running_services == total_services:
            console.print("\n✅ [bold green]All services are running normally![/bold green]")
        else:
            console.print(f"\n⚠️  [bold yellow]{running_services}/{total_services} services are running normally[/bold yellow]")

            
    except Exception as e:
        console.print(f"  [yellow]Service status check unavailable: {e}[/yellow]")
    
    # LLM Configuration Overview (from status command)
    console.print("\n🤖 [bold]LLM Configuration:[/bold]")
    
    try:
        from pixelle.settings import settings
        
        providers = settings.get_configured_llm_providers()
        if providers:
            console.print(f"🤖 [bold]LLM providers:[/bold] {', '.join(providers)} ({len(providers)} providers)")
            models = settings.get_all_available_models()
            console.print(f"📋 [bold]Available models:[/bold] {len(models)} models")
            console.print(f"⭐ [bold]Default model:[/bold] {settings.chainlit_chat_default_model}")
        else:
            console.print("⚠️  [bold yellow]Warning:[/bold yellow] No LLM providers configured")
            
    except Exception as e:
        console.print(f"  [yellow]LLM configuration check unavailable: {e}[/yellow]")
    
    # Workflow Overview (brief)
    console.print("\n🔧 [bold]Workflow Overview:[/bold]")
    
    try:
        from pixelle.utils.os_util import get_data_path
        from pixelle.manager.workflow_manager import workflow_manager
        
        # Get basic workflow stats
        custom_workflows_dir = Path(get_data_path("custom_workflows"))
        loaded_workflows = workflow_manager.loaded_workflows
        
        # Count workflow files
        custom_count = 0
        if custom_workflows_dir.exists():
            custom_count = len(list(custom_workflows_dir.glob("*.json")))
        
        active_tools = len(loaded_workflows)
        
        # Show summary
        console.print(f"📂 [bold]Custom Workflows:[/bold] {custom_count} files")
        console.print(f"⚡ [bold]Active MCP Tools:[/bold] {active_tools} tools")
        
        # Show active tools with signatures
        if loaded_workflows:
            console.print(f"\n💡 [bold]Available MCP Tools:[/bold]")
            sorted_tools = sorted(loaded_workflows.keys())
            for i, tool_name in enumerate(sorted_tools, 1):
                metadata = loaded_workflows[tool_name].get("metadata", {})
                params = metadata.get("params", {})
                
                # Create parameter signature with highlighting
                param_signatures = []
                for param_name, param_info in params.items():
                    param_type = param_info.get("type", "str")
                    required = param_info.get("required", False)
                    marker = "!" if required else "?"
                    # Highlight: param_name in cyan, type in yellow, marker in red/green
                    marker_color = "red" if required else "green"
                    param_sig = f"[cyan]{param_name}[/cyan]: [yellow]{param_type}[/yellow][{marker_color}]{marker}[/{marker_color}]"
                    param_signatures.append(param_sig)
                
                param_signature = ", ".join(param_signatures) if param_signatures else ""
                
                # Highlight tool name in bold cyan
                console.print(f"  {i:2d}. [bold cyan]{tool_name}[/bold cyan]({param_signature})")
        else:
            console.print("  [yellow]No MCP tools are currently loaded[/yellow]")
            
    except Exception as e:
        console.print(f"  [yellow]Workflow overview unavailable: {e}[/yellow]")
