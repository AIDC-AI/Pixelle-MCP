# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Display utility functions for CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_welcome():
    """Show welcome message"""
    welcome_text = """
🎨 [bold blue]Pixelle MCP 2.0[/bold blue]
A simple solution to convert ComfyUI workflow to MCP tool

✨ 30 seconds from zero to AI assistant
🔧 Zero code to convert workflow to MCP tool  
🌐 Support Cursor, Claude Desktop, etc. MCP clients
🤖 Support multiple mainstream LLMs (OpenAI, Ollama, Gemini, etc.)
"""
    
    console.print(Panel(
        welcome_text,
        title="Welcome to Pixelle MCP",
        border_style="blue",
        padding=(1, 2)
    ))


def show_header_info():
    """Show version and root path information"""
    # Show version information
    try:
        from pixelle import __version__
        console.print(f"🚀 [bold green]Pixelle Version:[/bold green] {__version__}")
    except ImportError:
        console.print("🚀 [bold yellow]Pixelle Version:[/bold yellow] unknown")
    
    # Show current root path
    from pixelle.utils.os_util import get_pixelle_root_path
    current_root_path = get_pixelle_root_path()
    console.print(f"🗂️  [bold blue]Root Path:[/bold blue] {current_root_path}")


def show_current_config():
    """Show current configuration"""
    from pixelle.settings import settings
    
    # Create configuration table
    table = Table(title="Current configuration", show_header=True, header_style="bold magenta")
    table.add_column("Configuration item", style="cyan", width=20)
    table.add_column("Current value", style="green")
    
    # Service configuration
    table.add_row("Service address", f"http://{settings.host}:{settings.port}")
    
    # Execution engines configuration
    if hasattr(settings, 'comfyui_base_url') and settings.comfyui_base_url:
        table.add_row("ComfyUI address", settings.comfyui_base_url)
    if hasattr(settings, 'runninghub_api_key') and settings.runninghub_api_key:
        table.add_row("RunningHub", "✅ Configured")
    
    # LLM configuration
    providers = settings.get_configured_llm_providers()
    if providers:
        table.add_row("LLM providers", ", ".join(providers))
        models = settings.get_all_available_models()
        if models:
            table.add_row("Available models", f"{len(models)} models")
            table.add_row("Default model", settings.chainlit_chat_default_model)
    else:
        table.add_row("LLM providers", "[red]Not configured[/red]")
    
    console.print(table)


def show_enhanced_help(ctx=None):
    """Show enhanced help information combining command list and help resources"""
    import typer
    
    # Show standard command help if context is available
    if ctx:
        console.print(ctx.get_help())
    
    # Show additional help resources
    console.print(Panel(
        "📚 [bold]More Help Resources[/bold]",
        title="Help Resources",
        border_style="blue",
        padding=(0, 1)
    ))
    
    console.print("• 📚 Documentation: https://github.com/AIDC-AI/Pixelle-MCP")
    console.print("• 🐛 Issue feedback: https://github.com/AIDC-AI/Pixelle-MCP/issues")
    console.print("• 💬 Community discussion: https://github.com/AIDC-AI/Pixelle-MCP#-community")
