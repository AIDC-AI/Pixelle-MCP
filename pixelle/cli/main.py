# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Main entry point for Pixelle CLI."""

import typer

from pixelle.cli.commands.interactive import interactive_command
from pixelle.cli.commands.start import start_command
from pixelle.cli.commands.stop import stop_command
from pixelle.cli.commands.status import status_command
from pixelle.cli.commands.logs import logs_command
from pixelle.cli.commands.init import init_command
from pixelle.cli.commands.edit import edit_command
from pixelle.cli.commands.workflow import workflow_app
from pixelle.cli.commands.dev import dev_command
from pixelle.cli.interactive.welcome import run_interactive_mode
from pixelle.cli.utils.display import show_enhanced_help

# Create typer app
app = typer.Typer(
    add_completion=False, 
    help="🎨 Pixelle MCP - A simple solution to convert ComfyUI workflow to MCP tool"
)

# Add callback for global options
@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    help: bool = typer.Option(False, "-h", "--help", help="Show help message and exit"),
):
    """Pixelle MCP CLI - Convert ComfyUI workflows to MCP tools"""
    if help:
        show_enhanced_help(ctx)
        raise typer.Exit()
    
    # If no subcommand is provided and not help, run interactive mode
    if ctx.invoked_subcommand is None and not help:
        # Import here to avoid circular imports
        import sys
        # If no command-line arguments (except script name), run interactive mode
        if len(sys.argv) == 1:
            run_interactive_mode()
        else:
            # Show help if command not recognized
            show_enhanced_help(ctx)
            raise typer.Exit()

# Add commands
app.command("interactive", hidden=False)(interactive_command)
app.command("start")(start_command)
app.command("stop")(stop_command)
app.command("status")(status_command)
app.command("logs")(logs_command)
app.command("init")(init_command)
app.command("edit")(edit_command)
app.add_typer(workflow_app, name="workflow")
app.command("dev")(dev_command)


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
