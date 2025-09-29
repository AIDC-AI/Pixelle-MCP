# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Execution engines configuration setup."""

from typing import Dict, Optional, Tuple
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .runninghub import setup_runninghub
from .comfyui import setup_comfyui

console = Console()


def show_engine_comparison():
    """Show comparison between execution engines"""
    console.print(Panel(
        "🔍 [bold]Execution Engine Comparison[/bold]",
        title="Learn More",
        border_style="blue"
    ))
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Feature", style="cyan", width=25)
    table.add_column("🌐 RunningHub Cloud", style="green", width=25)
    table.add_column("🏠 Local ComfyUI", style="yellow", width=25)
    
    table.add_row("Setup Difficulty", "⭐ Easy (No setup)", "⭐⭐⭐ Advanced")
    table.add_row("Hardware Requirements", "None (Cloud GPUs)", "High-end GPU recommended")
    table.add_row("Cost", "Pay per usage", "Free (your hardware)")
    table.add_row("Performance", "High-end cloud GPUs", "Depends on your hardware")
    table.add_row("Internet Required", "Yes", "No (after setup)")
    
    console.print(table)
    
    console.print("\n💡 [bold]Recommendations:[/bold]")
    console.print("• 🌟 [green]RunningHub[/green]: Perfect for beginners, quick prototyping, or users without powerful GPUs")
    console.print("• 🔧 [yellow]Local ComfyUI[/yellow]: Ideal for advanced users, custom workflows, or offline usage")
    console.print("• 🚀 [blue]Both[/blue]: Maximum flexibility - use cloud for quick tests, local for custom work")


def setup_execution_engines_interactive() -> Tuple[Optional[Dict], Optional[Dict]]:
    """Interactive setup for execution engines with full explanations"""
    console.print(Panel(
        "🚀 [bold]Choose Your Workflow Execution Engine[/bold]\n\n"
        "Pixelle MCP supports multiple ways to execute AI workflows:\n\n"
        "🌐 [bold cyan]RunningHub Cloud[/bold cyan] - Cloud-based execution (Recommended for beginners)\n"
        "   • No local setup required\n"
        "   • High-performance cloud GPUs\n"
        "   • Pre-configured AI models\n\n"
        "🏠 [bold yellow]Local ComfyUI[/bold yellow] - Local execution (For advanced users)\n"
        "   • Full control and customization\n"
        "   • Use your own hardware\n"
        "   • Offline execution capability\n\n"
        "🔄 [bold green]Both Engines[/bold green] - Maximum flexibility\n"
        "   • Switch between cloud and local as needed\n"
        "   • Redundancy and backup options",
        title="Step 1/4: Execution Engine Selection",
        border_style="blue"
    ))
    
    while True:
        engine_choice = questionary.select(
            "Which execution engine(s) would you like to configure?",
            choices=[
                questionary.Choice("🌐 RunningHub Cloud (Recommended for beginners)", "runninghub"),
                questionary.Choice("🏠 Local ComfyUI (For advanced users)", "comfyui"),
                questionary.Choice("🔄 Both engines (Maximum flexibility)", "both"),
                questionary.Choice("📚 Learn more about the differences", "learn"),
            ]
        ).ask()
        
        # Handle user cancellation (Ctrl+C)
        if engine_choice is None:
            raise KeyboardInterrupt("User cancelled execution engine selection")
        
        if engine_choice == "learn":
            show_engine_comparison()
            console.print("\n" + "="*80 + "\n")
            continue  # Show the selection again
        
        break
    
    runninghub_config = None
    comfyui_config = None
    
    # Configure selected engines
    try:
        if engine_choice in ["runninghub", "both"]:
            console.print("\n" + "─" * 60)
            runninghub_config = setup_runninghub()
            if not runninghub_config and engine_choice == "runninghub":
                console.print("⚠️  [yellow]No execution engine configured. At least one engine is required.[/yellow]")
                return setup_execution_engines_interactive()  # Retry
        
        if engine_choice in ["comfyui", "both"]:
            console.print("\n" + "─" * 60)
            comfyui_config = setup_comfyui_optional()
            if not comfyui_config and engine_choice == "comfyui":
                console.print("⚠️  [yellow]No execution engine configured. At least one engine is required.[/yellow]")
                return setup_execution_engines_interactive()  # Retry
    
    except KeyboardInterrupt:
        # If user cancels during engine configuration, propagate the cancellation
        raise
    
    # Validate that at least one engine is configured
    if not runninghub_config and not comfyui_config:
        console.print("❌ [red]At least one execution engine must be configured![/red]")
        return setup_execution_engines_interactive()  # Retry
    
    return runninghub_config, comfyui_config




def setup_comfyui_optional() -> Optional[Dict]:
    """Setup ComfyUI as optional component"""
    console.print(Panel(
        "🏠 [bold]Local ComfyUI Configuration[/bold]\n\n"
        "Configure connection to your local ComfyUI installation.\n"
        "If you don't have ComfyUI installed yet, visit:\n"
        "https://github.com/comfyanonymous/ComfyUI\n\n"
        "⚠️  [yellow]Note:[/yellow] This requires a local ComfyUI server running on your machine.",
        title="Local ComfyUI Setup",
        border_style="yellow"
    ))
    
    # Use existing ComfyUI setup function
    return setup_comfyui()
