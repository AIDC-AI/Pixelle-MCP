# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Logs command implementation."""

import typer
from pathlib import Path
from rich.console import Console

console = Console()


def logs_command(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output continuously"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show from the end"),
):
    """📄 View Pixelle MCP service logs"""
    
    from pixelle.utils.os_util import get_pixelle_root_path
    root_path = Path(get_pixelle_root_path())
    logs_dir = root_path / "logs"
    log_file = logs_dir / "pixelle.log"
    
    if not log_file.exists():
        console.print("❌ [red]Log file not found[/red]")
        console.print(f"Expected location: {log_file}")
        console.print("💡 Make sure the service has been started at least once in daemon mode")
        return
    
    try:
        if follow:
            # Follow mode - use subprocess to call tail
            console.print(f"📄 [bold]Following log file: {log_file}[/bold]")
            console.print("Press [bold]Ctrl+C[/bold] to stop following\n")
            
            import subprocess
            import sys
            
            try:
                # Use tail -f on Unix systems
                if sys.platform != "win32":
                    subprocess.run(["tail", "-f", str(log_file)])
                else:
                    # For Windows, implement a simple follow mechanism
                    import time
                    
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Go to end of file
                        f.seek(0, 2)
                        
                        while True:
                            line = f.readline()
                            if line:
                                console.print(line.rstrip())
                            else:
                                time.sleep(0.1)  # Sleep briefly
                                
            except KeyboardInterrupt:
                console.print("\n👋 Stopped following logs")
        else:
            # Show last N lines
            console.print(f"📄 [bold]Last {lines} lines from: {log_file}[/bold]\n")
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                if len(all_lines) > lines:
                    display_lines = all_lines[-lines:]
                else:
                    display_lines = all_lines
                
                for line in display_lines:
                    console.print(line.rstrip())
            
            console.print(f"\n💡 Use [cyan]pixelle logs --follow[/cyan] (or [cyan]-f[/cyan]) to follow logs in real-time")
            
    except Exception as e:
        console.print(f"❌ [red]Error reading log file: {e}[/red]")
