# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Server management utility functions."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pixelle.settings import settings
from pixelle.utils.process_util import (
    check_port_in_use,
    get_process_using_port,
    kill_process_on_port,
)
from pixelle.utils.network_util import (
    check_mcp_streamable,
    test_comfyui_connection,
    check_url_status,
)

console = Console()


def start_pixelle_server(daemon: bool = False, force: bool = False):
    """Start Pixelle server"""
    console.print("\n🚀 [bold]Starting Pixelle MCP...[/bold]")
    
    try:
        # Reload environment variables from root path
        from dotenv import load_dotenv
        from pathlib import Path
        from pixelle.utils.os_util import get_pixelle_root_path
        
        # Load from .env file in root path
        root_path = get_pixelle_root_path()
        env_path = Path(root_path) / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        
        port = int(settings.port)
        
        # Check if port is in use
        if check_port_in_use(port):
            process_info = get_process_using_port(port)
            
            if not force:
                # Without --force, report error and exit
                console.print(f"❌ [bold red]Port {port} is already in use[/bold red]")
                if process_info:
                    console.print(f"Occupied by process: {process_info}")
                console.print(f"💡 Use [cyan]pixelle start --force[/cyan] (or [cyan]-f[/cyan]) to terminate the existing process and start")
                console.print(f"💡 Or use [cyan]pixelle stop[/cyan] to stop the existing service first")
                raise typer.Exit(1)
            
            # With --force, attempt to kill existing process
            console.print(f"🔄 [bold yellow]Force mode: Terminating existing process on port {port}[/bold yellow]")
            if process_info:
                console.print(f"Target process: {process_info}")
            
            if kill_process_on_port(port):
                console.print("✅ Existing process terminated")
                import time
                time.sleep(2)  # Wait for port to be released
            else:
                console.print("❌ [bold red]Failed to terminate existing process[/bold red]")
                console.print("💡 You may need to manually stop the conflicting service")
                raise typer.Exit(1)
        
        # Start service
        if daemon:
            # Daemon mode
            import subprocess
            import sys
            import os
            from pathlib import Path
            
            # Get project root and create necessary directories
            from pixelle.utils.os_util import get_pixelle_root_path
            root_path = Path(get_pixelle_root_path())
            logs_dir = root_path / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            pid_file = root_path / ".pixelle.pid"
            log_file = logs_dir / "pixelle.log"
            
            # Check if already running
            if pid_file.exists():
                try:
                    with open(pid_file, 'r') as f:
                        existing_pid = int(f.read().strip())
                    # Check if process is still running
                    import psutil
                    if psutil.pid_exists(existing_pid):
                        if not force:
                            console.print(f"❌ [bold red]Pixelle daemon is already running (PID: {existing_pid})[/bold red]")
                            console.print("💡 Use [cyan]pixelle start --force[/cyan] (or [cyan]-f[/cyan]) to terminate and restart")
                            console.print("💡 Or use [cyan]pixelle stop[/cyan] to stop the existing service first")
                            raise typer.Exit(1)
                        else:
                            # Force mode: terminate existing daemon
                            console.print(f"🔄 [bold yellow]Force mode: Terminating existing daemon (PID: {existing_pid})[/bold yellow]")
                            try:
                                process = psutil.Process(existing_pid)
                                process.terminate()
                                try:
                                    process.wait(timeout=10)
                                    console.print("✅ Existing daemon terminated")
                                except psutil.TimeoutExpired:
                                    process.kill()
                                    process.wait()
                                    console.print("✅ Existing daemon force killed")
                            except psutil.NoSuchProcess:
                                console.print("ℹ️  Process already stopped")
                            
                            # Clean up PID file
                            pid_file.unlink()
                            import time
                            time.sleep(1)  # Wait for cleanup
                except (ValueError, FileNotFoundError):
                    pass  # Invalid or missing PID file, continue
            
            # Start daemon process
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    [sys.executable, "-m", "pixelle.main"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=root_path,
                    start_new_session=True  # Detach from parent
                )
            
            # Save PID
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            console.print(Panel(
                f"🌐 Web interface: http://localhost:{settings.port}/\n"
                f"🔌 MCP endpoint: http://localhost:{settings.port}/pixelle/mcp\n"
                f"📁 Loaded workflow directory: data/custom_workflows/\n"
                f"📋 PID: {process.pid}\n"
                f"📄 Log file: {log_file}",
                title="🎉 Pixelle MCP started in daemon mode!",
                border_style="green"
            ))
            
            console.print(f"\n💡 [bold]Management commands:[/bold]")
            console.print("  • [cyan]pixelle status[/cyan] - Check service status")
            console.print("  • [cyan]pixelle stop[/cyan] - Stop the service")
            console.print("  • [cyan]pixelle start --force --daemon[/cyan] (or [cyan]-fd[/cyan]) - Force restart")
            console.print(f"  • [cyan]pixelle logs --follow[/cyan] (or [cyan]-f[/cyan]) - Follow logs")
            console.print(f"  • [cyan]tail -f {log_file}[/cyan] - View logs (alternative)")
            
        else:
            # Foreground mode
            console.print(Panel(
                f"🌐 Web interface: http://localhost:{settings.port}/\n"
                f"🔌 MCP endpoint: http://localhost:{settings.port}/pixelle/mcp\n"
                f"📁 Loaded workflow directory: data/custom_workflows/",
                title="🎉 Pixelle MCP is running!",
                border_style="green"
            ))
            
            console.print("\nPress [bold]Ctrl+C[/bold] to stop service\n")
            
            # Import and start main
            from pixelle.main import main as start_main
            start_main()
        
    except KeyboardInterrupt:
        console.print("\n👋 Pixelle MCP stopped")
    except Exception as e:
        console.print(f"❌ Launch failed: {e}")


def check_service_status():
    """Check service status"""
    console.print(Panel(
        "📋 [bold]Check service status[/bold]\n\n"
        "Checking the status of all services...",
        title="Service status check",
        border_style="cyan"
    ))
    
    import requests
    
    # Create status table
    status_table = Table(title="Service status", show_header=True, header_style="bold cyan")
    status_table.add_column("Service", style="cyan", width=20)
    status_table.add_column("Address", style="yellow", width=40)
    status_table.add_column("Status", width=15)
    status_table.add_column("Description", style="white")
    
    # Check MCP endpoint
    pixelle_url = f"http://{settings.host}:{settings.port}"
    pixelle_mcp_server_url = f"{pixelle_url}/pixelle/mcp"
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
    
    # Check execution engines
    engines_checked = 0
    engines_working = 0
    
    # Check ComfyUI if configured
    if hasattr(settings, 'comfyui_base_url') and settings.comfyui_base_url:
        engines_checked += 1
        comfyui_status = test_comfyui_connection(settings.comfyui_base_url)
        if comfyui_status:
            engines_working += 1
        status_table.add_row(
            "ComfyUI (Local)",
            settings.comfyui_base_url,
            "🟢 Connected" if comfyui_status else "🔴 Connection failed",
            "Local workflow execution" if comfyui_status else "Please check if ComfyUI is running"
        )
    
    # Check RunningHub if configured
    if hasattr(settings, 'runninghub_api_key') and settings.runninghub_api_key:
        engines_checked += 1
        # For RunningHub, we just check if API key is configured
        # Actual connectivity would require an API call
        runninghub_status = True  # Assume configured means working
        if runninghub_status:
            engines_working += 1
        status_table.add_row(
            "RunningHub (Cloud)",
            "Cloud API",
            "🟢 Configured" if runninghub_status else "🔴 Not configured",
            "Cloud workflow execution" if runninghub_status else "Please configure RunningHub API key"
        )
    
    console.print(status_table)
    
    # Show LLM configuration status
    providers = settings.get_configured_llm_providers()
    if providers:
        console.print(f"\n🤖 [bold]LLM providers:[/bold] {', '.join(providers)} ({len(providers)} providers)")
        models = settings.get_all_available_models()
        console.print(f"📋 [bold]Available models:[/bold] {len(models)} models")
        console.print(f"⭐ [bold]Default model:[/bold] {settings.chainlit_chat_default_model}")
    else:
        console.print("\n⚠️  [bold yellow]Warning:[/bold yellow] No LLM providers configured")
    
    # Summary
    core_services = 2  # MCP, Web
    total_services = core_services + engines_checked
    running_services = sum([mcp_status, web_status]) + engines_working
    
    if running_services == total_services:
        console.print("\n✅ [bold green]All services are running normally![/bold green]")
    else:
        console.print(f"\n⚠️  [bold yellow]{running_services}/{total_services} services are running normally[/bold yellow]")
        if engines_checked == 0:
            console.print("⚠️  [bold yellow]No execution engines configured! Please run [cyan]pixelle init[/cyan] to configure ComfyUI or RunningHub[/bold yellow]")
        else:
            console.print("💡 If any service is not running, please check the configuration or restart the service")
