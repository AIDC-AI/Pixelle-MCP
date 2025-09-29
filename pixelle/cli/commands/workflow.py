# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Workflow command implementation."""

import typer
import json
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm
import questionary

console = Console()

# Create workflow sub-app
workflow_app = typer.Typer(help="🔧 Workflow management commands")


def workflow_command():
    """🔧 Workflow management commands"""
    workflow_app()


@workflow_app.command("list")
def list_workflows(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by workflow source: 'local', 'runninghub', or 'all'")
):
    """📋 Display all current workflow files and tools information"""
    
    # Show header information
    from pixelle.cli.utils.display import show_header_info
    show_header_info()
    
    # Get root path for workflow directories
    from pixelle.utils.os_util import get_pixelle_root_path, get_data_path
    current_root_path = get_pixelle_root_path()
    
    # Get workflow directories
    builtin_workflows_dir = Path(current_root_path) / "workflows"
    custom_workflows_dir = Path(get_data_path("custom_workflows"))
    
    console.print(Panel(
        f"📁 [bold]Custom Workflows:[/bold] {custom_workflows_dir}",
        title="Workflow Directories",
        border_style="cyan"
    ))
    
    # Get loaded workflow manager info
    try:
        from pixelle.manager.workflow_manager import workflow_manager
        loaded_workflows = workflow_manager.loaded_workflows
        total_loaded = len(loaded_workflows)
    except Exception as e:
        console.print(f"⚠️  Cannot access workflow manager: {e}")
        loaded_workflows = {}
        total_loaded = 0
    
    # Loaded Tools Details Table
    if loaded_workflows:
        loaded_table = Table(title="⚡ Currently Loaded MCP Tools", show_header=True, header_style="bold blue")
        loaded_table.add_column("Tool Name", style="cyan", width=16)
        loaded_table.add_column("Source", style="magenta", width=10)
        loaded_table.add_column("Parameters", style="yellow", width=20)
        loaded_table.add_column("Description", style="white", width=26)
        loaded_table.add_column("Created", style="green", width=16)
        loaded_table.add_column("Modified", style="blue", width=16)
        
        for tool_name, tool_info in loaded_workflows.items():
            metadata = tool_info.get("metadata", {})
            
            # Filter by source if specified
            workflow_source = metadata.get("source", "local")
            if source and source != "all":
                if source == "local" and workflow_source not in ["local", "comfyui"]:
                    continue
                elif source == "runninghub" and workflow_source != "runninghub":
                    continue
            description = metadata.get("description", "No description")
            if not description or description == "No description":
                description = "[dim]No description[/dim]"
            else:
                # Limit description length to avoid overly tall rows
                max_length = 100  # Adjust based on column width
                if len(description) > max_length:
                    description = description[:max_length-3] + "..."
            
            # Format parameters - each parameter on a new line
            params = metadata.get("params", {})
            if params:
                param_lines = []
                for param_name, param_info in params.items():
                    param_type = param_info.get("type", "str")
                    required = param_info.get("required", False)
                    marker = "!" if required else "?"
                    param_lines.append(f"{param_name}({param_type}){marker}")
                param_display = "\n".join(param_lines)
            else:
                param_display = "No params"
            
            # Determine workflow source display
            workflow_source = metadata.get("source", "local")
            if workflow_source == "runninghub":
                source_display = "🌐 Cloud"
            else:
                source_display = "🏠 Local"
            
            # Get file creation and modification times
            workflow_file = custom_workflows_dir / f"{tool_name}.json"
            if workflow_file.exists():
                file_stat = workflow_file.stat()
                created_time = datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M")
                modified_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            else:
                created_time = "Unknown"
                modified_time = "Unknown"
            
            loaded_table.add_row(tool_name, source_display, param_display, description, created_time, modified_time)
        
        console.print(loaded_table)
        
        # Simple summary
        active_tools = len(loaded_workflows)
        console.print(f"\n📊 [bold]Total Active MCP Tools:[/bold] {active_tools}")
    else:
        console.print("⚡ [yellow]No MCP tools are currently loaded[/yellow]")


@workflow_app.command("install")
def install_examples():
    """📥 Install workflow examples from the built-in collection"""
    
    from pixelle.utils.os_util import get_src_path, get_data_path
    
    # Get built-in workflows directory from package
    # The workflows directory should be included in the package
    builtin_workflows_dir = Path(get_src_path("workflows"))
    
    # If not found in package, try parent directory (development mode)
    if not builtin_workflows_dir.exists():
        builtin_workflows_dir = Path(get_src_path()) / ".." / "workflows"
        builtin_workflows_dir = builtin_workflows_dir.resolve()
    
    if not builtin_workflows_dir.exists():
        console.print("❌ [red]Built-in workflows directory not found![/red]")
        console.print(f"   Expected path: {builtin_workflows_dir}")
        return
    
    # Get custom workflows directory
    custom_workflows_dir = Path(get_data_path("custom_workflows"))
    
    console.print(Panel(
        f"📦 [bold]Built-in Workflows:[/bold] {builtin_workflows_dir}\n"
        f"📁 [bold]Install Location:[/bold] {custom_workflows_dir}",
        title="Workflow Installation",
        border_style="cyan"
    ))
    
    # Scan built-in workflows
    workflow_files = list(builtin_workflows_dir.glob("*.json"))
    if not workflow_files:
        console.print("❌ [red]No built-in workflow files found![/red]")
        return
    
    # Parse workflow metadata and create choices
    workflow_choices = []
    workflow_info = {}
    
    for workflow_file in workflow_files:
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            # Extract metadata
            metadata = workflow_data.get("metadata", {})
            name = workflow_file.stem
            description = metadata.get("description", "No description available")
            category = metadata.get("category", "General")
            
            # Check if already installed
            target_file = custom_workflows_dir / workflow_file.name
            is_installed = target_file.exists()
            status = "✅ Installed" if is_installed else "📦 Available"
            
            workflow_info[name] = {
                "file": workflow_file,
                "description": description,
                "category": category,
                "installed": is_installed
            }
            
            # Create choice display
            choice_text = f"{status} [{category}] {name}"
            if len(description) > 50:
                choice_text += f" - {description[:47]}..."
            else:
                choice_text += f" - {description}"
                
            workflow_choices.append(questionary.Choice(choice_text, name))
            
        except Exception as e:
            console.print(f"⚠️  Failed to parse {workflow_file.name}: {e}")
            continue
    
    if not workflow_choices:
        console.print("❌ [red]No valid workflow files found![/red]")
        return
    
    # Show available workflows in a table first
    table = Table(title="📦 Available Example Workflows", show_header=True, header_style="bold blue")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Category", style="yellow", width=12)
    table.add_column("Status", style="green", width=12)
    table.add_column("Description", style="white", width=40)
    
    for name, info in workflow_info.items():
        status = "✅ Installed" if info["installed"] else "📦 Available"
        description = info["description"]
        if len(description) > 40:
            description = description[:37] + "..."
        table.add_row(name, info["category"], status, description)
    
    console.print(table)
    
    # Multi-select workflow installation
    console.print("\n🎯 [bold]Select workflows to install:[/bold]")
    selected_workflows = questionary.checkbox(
        "Choose workflows (use space to select, enter to confirm):",
        choices=workflow_choices
    ).ask()
    
    if not selected_workflows:
        console.print("❌ No workflows selected. Operation cancelled.")
        return
    
    # Install selected workflows
    console.print(f"\n🚀 Installing {len(selected_workflows)} workflow(s)...")
    
    installed_count = 0
    skipped_count = 0
    
    for workflow_name in selected_workflows:
        info = workflow_info[workflow_name]
        source_file = info["file"]
        target_file = custom_workflows_dir / source_file.name
        
        if info["installed"]:
            # Ask for overwrite confirmation
            if not Confirm.ask(f"🔄 {workflow_name} is already installed. Overwrite?", default=False):
                console.print(f"⏭️  Skipped: {workflow_name}")
                skipped_count += 1
                continue
        
        try:
            # Copy workflow file
            shutil.copy2(source_file, target_file)
            console.print(f"✅ Installed: {workflow_name}")
            installed_count += 1
        except Exception as e:
            console.print(f"❌ Failed to install {workflow_name}: {e}")
    
    # Summary
    console.print(f"\n📊 [bold]Installation Summary:[/bold]")
    console.print(f"   ✅ Installed: {installed_count}")
    if skipped_count > 0:
        console.print(f"   ⏭️  Skipped: {skipped_count}")
    
    if installed_count > 0:
        console.print(f"\n💡 [bold yellow]New workflows installed successfully![/bold yellow]")
        console.print("🔄 [bold red]Please restart Pixelle service to load the new MCP tools.[/bold red]")


@workflow_app.command("open")
def open_workflows_folder():
    """📁 Open the custom workflows folder in file manager"""
    
    from pixelle.utils.os_util import get_data_path
    
    custom_workflows_dir = Path(get_data_path("custom_workflows"))
    
    console.print(Panel(
        f"📁 [bold]Custom Workflows Directory:[/bold]\n{custom_workflows_dir}",
        title="Workflow Folder",
        border_style="cyan"
    ))
    
    if not custom_workflows_dir.exists():
        console.print("❌ [red]Custom workflows directory does not exist![/red]")
        console.print("💡 [yellow]Run 'pixelle workflow browse' to install some example workflows first.[/yellow]")
        return
    
    try:
        # Detect OS and open file manager
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            subprocess.run(["open", str(custom_workflows_dir)], check=True)
            console.print("🍎 [green]Opened in Finder (macOS)[/green]")
        elif system == "windows":  # Windows
            subprocess.run(["explorer", str(custom_workflows_dir)], check=True)
            console.print("🪟 [green]Opened in File Explorer (Windows)[/green]")
        elif system == "linux":  # Linux
            # Try common Linux file managers
            file_managers = ["xdg-open", "nautilus", "dolphin", "thunar", "pcmanfm"]
            for fm in file_managers:
                try:
                    subprocess.run([fm, str(custom_workflows_dir)], check=True)
                    console.print(f"🐧 [green]Opened with {fm} (Linux)[/green]")
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            else:
                # Fallback: print the path
                console.print("🐧 [yellow]Could not auto-open file manager. Path copied above.[/yellow]")
        else:
            console.print(f"❓ [yellow]Unknown OS: {system}. Path copied above.[/yellow]")
            
    except subprocess.CalledProcessError as e:
        console.print(f"❌ [red]Failed to open file manager: {e}[/red]")
        console.print("💡 [yellow]You can manually navigate to the path shown above.[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")


@workflow_app.command("add-runninghub")
def add_runninghub_workflow(
    workflow_id: str = typer.Argument(..., help="RunningHub workflow ID"),
    tool_name: str = typer.Argument(..., help="Tool name for the workflow (must be valid Python identifier)")
):
    """📥 Add a workflow from RunningHub by workflow ID"""
    
    from pixelle.cli.utils.display import show_header_info
    show_header_info()
    
    console.print(Panel(
        f"🌐 [bold]Adding RunningHub Workflow[/bold]\n\n"
        f"Workflow ID: {workflow_id}\n"
        f"Tool Name: {tool_name}",
        title="RunningHub Workflow",
        border_style="cyan"
    ))
    
    try:
        # Import the RunningHub workflow handling function
        import asyncio
        from pixelle.utils.runninghub_util import handle_runninghub_workflow_save
        
        # Run the async function
        result = asyncio.run(handle_runninghub_workflow_save(workflow_id, tool_name))
        
        if result["success"]:
            console.print("✅ [bold green]RunningHub workflow added successfully![/bold green]")
            console.print(f"📁 [bold]Workflow file:[/bold] {result['workflow_file_path']}")
            console.print("💡 Run [bold]pixelle start[/bold] to load the new tool")
        else:
            console.print(f"❌ [bold red]Failed to add RunningHub workflow:[/bold red] {result['error']}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [bold red]Error adding RunningHub workflow:[/bold red] {e}")
        raise typer.Exit(1)


def show_workflow_menu():
    """Show interactive workflow management menu"""
    from pixelle.cli.utils.display import show_header_info
    
    # Show header
    show_header_info()
    
    console.print(Panel(
        "🔧 [bold]Workflow Management[/bold]\n"
        "Choose an action to manage your ComfyUI workflows:",
        title="Workflow Menu",
        border_style="blue"
    ))
    
    while True:
        try:
            # Create menu choices
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    questionary.Choice("📋 List Current MCP Tools", "list"),
                    questionary.Choice("🌐 Add RunningHub Workflow", "add_runninghub"),
                    questionary.Choice("📥 Install Workflow Examples", "install"), 
                    questionary.Choice("📁 Open Workflows Folder", "open"),
                    questionary.Choice("❌ Exit", "exit")
                ],
                style=questionary.Style([
                    ('question', 'bold'),
                    ('answer', 'fg:#ff9d00 bold'),
                    ('pointer', 'fg:#ff9d00 bold'),
                    ('highlighted', 'fg:#ff9d00 bold'),
                    ('selected', 'fg:#cc5454'),
                    ('separator', 'fg:#cc5454'),
                    ('instruction', ''),
                    ('text', ''),
                ])
            ).ask()
            
            if choice is None or choice == "exit":
                console.print("👋 [bold]Goodbye![/bold]")
                break
            elif choice == "list":
                console.print("\n" + "="*80 + "\n")
                list_workflows()
                console.print("\n" + "="*80 + "\n")
            elif choice == "add_runninghub":
                console.print("\n" + "="*80 + "\n")
                # Interactive RunningHub workflow addition
                workflow_id = questionary.text("Enter RunningHub workflow ID:").ask()
                if workflow_id:
                    tool_name = questionary.text("Enter tool name (must be valid Python identifier):").ask()
                    if tool_name:
                        add_runninghub_workflow(workflow_id, tool_name)
                    else:
                        console.print("⚠️  Tool name is required")
                else:
                    console.print("⚠️  Workflow ID is required")
                console.print("\n" + "="*80 + "\n")
            elif choice == "install":
                console.print("\n" + "="*80 + "\n")
                install_examples()
                console.print("\n" + "="*80 + "\n")
            elif choice == "open":
                console.print("\n" + "="*80 + "\n")
                open_workflows_folder()
                console.print("\n" + "="*80 + "\n")
            
            # Ask if user wants to continue
            if choice != "exit":
                if not questionary.confirm("Continue with workflow management?", default=True).ask():
                    console.print("👋 [bold]Goodbye![/bold]")
                    break
                    
        except KeyboardInterrupt:
            console.print("\n👋 [bold]Goodbye![/bold]")
            break
        except Exception as e:
            console.print(f"❌ [red]Error: {e}[/red]")
            break


# Default command (when no subcommand is specified)
@workflow_app.callback(invoke_without_command=True)
def workflow_default(ctx: typer.Context):
    """🔧 Workflow management - interactive menu"""
    if ctx.invoked_subcommand is None:
        # Show interactive menu
        show_workflow_menu()

