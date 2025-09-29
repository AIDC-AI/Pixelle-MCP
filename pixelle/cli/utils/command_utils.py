# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Command-line utility functions."""

from pathlib import Path
from rich.console import Console

console = Console()



def detect_config_status() -> str:
    """Detect current config status"""
    from pixelle.utils.os_util import get_pixelle_root_path
    pixelle_root = get_pixelle_root_path()
    env_file = Path(pixelle_root) / ".env"
    
    if not env_file.exists():
        return "first_time"
    
    # Check if .env is a directory (common Docker issue)
    if env_file.is_dir():
        from rich.console import Console
        console = Console()
        console.print("\n❌ [bold red]Configuration Error: .env is a directory![/bold red]")
        console.print("💡 This happens when Docker creates a directory instead of mounting a file")
        console.print("\n🔧 [bold]Fix steps:[/bold]")
        console.print("   1. Stop container: [cyan]docker compose down[/cyan]")
        console.print("   2. Remove .env directory: [cyan]rm -rf .env[/cyan]") 
        console.print("   3. Create .env file with configuration")
        console.print("   4. Restart: [cyan]docker compose up[/cyan]")
        console.print("\n💡 Use .env.example as template")
        raise SystemExit(1)
    
    # Parse env file
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"\'')
    
    # Use the centralized config validation logic
    from pixelle.utils.config_util import detect_config_status_from_env
    return detect_config_status_from_env(env_vars)
