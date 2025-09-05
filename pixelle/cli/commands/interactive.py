# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Interactive command implementation."""

from rich.console import Console

from pixelle.cli.interactive.welcome import run_interactive_mode

console = Console()


def interactive_command():
    """🎨 Run in interactive mode (default when no command specified)"""
    
    # Run interactive mode
    run_interactive_mode()
