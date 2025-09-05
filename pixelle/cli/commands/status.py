# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Status command implementation."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def status_command():
    """📊 Check the status of Pixelle MCP service and dependencies"""
    
    # Show header information
    from pixelle.cli.utils.display import show_header_info
    show_header_info()
    
    console.print("📊 [bold]Checking Pixelle MCP service status...[/bold]\n")
    
    # Check daemon process status
    from pixelle.utils.os_util import get_pixelle_root_path
    root_path = Path(get_pixelle_root_path())
    pid_file = root_path / ".pixelle.pid"
    
    daemon_running = False
    daemon_pid = None
    
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            import psutil
            if psutil.pid_exists(pid):
                try:
                    process = psutil.Process(pid)
                    daemon_running = True
                    daemon_pid = pid
                    console.print(f"🟢 [green]Daemon process running (PID: {pid}, Name: {process.name()})[/green]")
                except psutil.NoSuchProcess:
                    console.print("🔴 [red]Daemon process not found, cleaning up PID file[/red]")
                    pid_file.unlink()
            else:
                console.print("🔴 [red]Daemon process not running, cleaning up PID file[/red]")
                pid_file.unlink()
        except (ValueError, FileNotFoundError):
            console.print("🔴 [red]Invalid or missing PID file[/red]")
            if pid_file.exists():
                pid_file.unlink()
    else:
        console.print("🔴 [red]No daemon process running[/red]")
    
    # Check configuration status
    console.print("\n🔧 [bold]Configuration Status:[/bold]")
    try:
        from pixelle.cli.utils.command_utils import detect_config_status
        config_status = detect_config_status()
        
        if config_status == "configured":
            console.print("✅ [green]Configuration is complete and valid[/green]")
        elif config_status == "incomplete":
            console.print("⚠️  [yellow]Configuration is incomplete[/yellow]")
        else:
            console.print("❌ [red]No configuration found[/red]")
    except Exception as e:
        console.print(f"❌ [red]Configuration check failed: {e}[/red]")
    
    # Check service endpoints (only if we think something should be running)
    console.print("\n🌐 [bold]Service Endpoints:[/bold]")
    try:
        # Reload config to ensure we have latest settings
        from pixelle.cli.setup.config_saver import reload_config
        reload_config()
        
        from pixelle.settings import settings
        from pixelle.utils.network_util import check_url_status, check_mcp_streamable, test_comfyui_connection
        
        # Create status table
        status_table = Table(show_header=True, header_style="bold blue")
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
            "MCP protocol endpoint" if mcp_status else "Service not responding"
        )
        
        # Check Web interface
        web_status = check_url_status(pixelle_url)
        status_table.add_row(
            "Web interface",
            pixelle_url,
            "🟢 Available" if web_status else "🔴 Unavailable",
            "Chat interface" if web_status else "Service not responding"
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
        total_services = 2  # MCP, Web (ComfyUI is external)
        running_services = sum([mcp_status, web_status])
        
        console.print(f"\n📈 [bold]Service Summary:[/bold] {running_services}/{total_services} core services running")
        
        if comfyui_status:
            console.print("✅ [green]ComfyUI dependency is also available[/green]")
        else:
            console.print("⚠️  [yellow]ComfyUI dependency is not available[/yellow]")
        
    except Exception as e:
        console.print(f"❌ [red]Service endpoint check failed: {e}[/red]")
    
    # Show log file information
    console.print("\n📄 [bold]Log Files:[/bold]")
    try:
        logs_dir = root_path / "logs"
        if logs_dir.exists():
            log_file = logs_dir / "pixelle.log"
            if log_file.exists():
                # Get log file size
                file_size = log_file.stat().st_size
                size_str = f"{file_size:,} bytes"
                if file_size > 1024 * 1024:
                    size_str = f"{file_size / (1024*1024):.1f} MB"
                elif file_size > 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                
                console.print(f"📄 Log file: {log_file} ({size_str})")
                console.print(f"💡 View logs: [cyan]tail -f {log_file}[/cyan]")
            else:
                console.print("📄 No log file found")
        else:
            console.print("📄 Logs directory not found")
    except Exception as e:
        console.print(f"❌ [red]Log file check failed: {e}[/red]")
    
    # Show management commands
    console.print("\n💡 [bold]Management Commands:[/bold]")
    if daemon_running:
        console.print("  • [cyan]pixelle stop[/cyan] - Stop the service")
        console.print("  • [cyan]pixelle start --force --daemon[/cyan] (or [cyan]-fd[/cyan]) - Force restart in background")
    else:
        console.print("  • [cyan]pixelle start[/cyan] - Start in foreground")
        console.print("  • [cyan]pixelle start --daemon[/cyan] (or [cyan]-d[/cyan]) - Start in background")
        console.print("  • [cyan]pixelle start --force[/cyan] (or [cyan]-f[/cyan]) - Force start (kill conflicting processes)")
    console.print("  • [cyan]pixelle dev[/cyan] - Show detailed debugging information")
