# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Start command implementation."""

import typer
from rich.console import Console

from pixelle.cli.utils.command_utils import detect_config_status
from pixelle.cli.utils.server_utils import start_pixelle_server

console = Console()


def start_command(
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Run in background daemon mode"),
    force: bool = typer.Option(False, "--force", "-f", help="Force start by terminating existing processes"),
):
    """🚀 Start Pixelle MCP server directly (non-interactive)"""
    
    # Show header information
    from pixelle.cli.utils.display import show_header_info
    show_header_info()
    
    # Check if configuration exists
    config_status = detect_config_status()
    
    if config_status == "first_time":
        console.print("❌ [bold red]No configuration found![/bold red]")


        raise typer.Exit(1)
    elif config_status == "incomplete":
        console.print("❌ [bold red]Configuration is incomplete![/bold red]")


        raise typer.Exit(1)
    
    # Start server directly
    start_pixelle_server(daemon=daemon, force=force)
