# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Stop command implementation."""

import typer
from pathlib import Path
from rich.console import Console

console = Console()


def stop_command():
    """🛑 Stop the running Pixelle MCP service"""
    
    from pixelle.utils.os_util import get_pixelle_root_path
    root_path = Path(get_pixelle_root_path())
    pid_file = root_path / ".pixelle.pid"
    
    if not pid_file.exists():
        console.print("ℹ️  [yellow]No running Pixelle service found[/yellow]")
        return
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        import psutil
        if not psutil.pid_exists(pid):
            console.print(f"⚠️  [yellow]Process {pid} is not running, cleaning up PID file[/yellow]")
            pid_file.unlink()
            return
        
        # Get process info for confirmation
        try:
            process = psutil.Process(pid)
            console.print(f"🔍 Found running process: PID {pid} ({process.name()})")
        except psutil.NoSuchProcess:
            console.print(f"⚠️  [yellow]Process {pid} is not running, cleaning up PID file[/yellow]")
            pid_file.unlink()
            return
        
        # Terminate the process
        console.print(f"🛑 Stopping Pixelle MCP service (PID: {pid})...")
        
        try:
            process.terminate()  # Send SIGTERM
            try:
                process.wait(timeout=10)  # Wait up to 10 seconds for graceful shutdown
                console.print("✅ [green]Service stopped gracefully[/green]")
            except psutil.TimeoutExpired:
                console.print("⚠️  [yellow]Graceful shutdown timed out, force killing...[/yellow]")
                process.kill()  # Send SIGKILL
                process.wait()  # Wait for force kill
                console.print("✅ [green]Service force stopped[/green]")
                
        except psutil.NoSuchProcess:
            console.print("ℹ️  [yellow]Process already stopped[/yellow]")
        
        # Clean up PID file
        pid_file.unlink()
        console.print("🧹 Cleaned up PID file")
        
    except (ValueError, FileNotFoundError) as e:
        console.print(f"❌ [red]Error reading PID file: {e}[/red]")
        # Try to clean up invalid PID file
        if pid_file.exists():
            pid_file.unlink()
            console.print("🧹 Cleaned up invalid PID file")
    
    except Exception as e:
        console.print(f"❌ [red]Error stopping service: {e}[/red]")
