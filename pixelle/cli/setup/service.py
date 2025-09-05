# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Service configuration setup."""

from typing import Dict, Optional
import socket
import questionary
from rich.console import Console
from rich.panel import Panel



console = Console()


def setup_service_config() -> Optional[Dict]:
    """Configure service options - Step 3"""
    console.print(Panel(
        "⚙️ [bold]Service configuration[/bold]\n\n"
        "Configure Pixelle MCP service options, including port, host address, etc.",
        title="Step 3/4: Service configuration",
        border_style="yellow"
    ))
    
    default_port = "9004"
    port = questionary.text(
        "Service port:",
        default=default_port,
        instruction="(press Enter to use default port 9004, or input other port)"
    ).ask()
    
    if not port:
        port = default_port
    
    console.print(f"✅ Service will start on port {port}")
    
    # Configure host address
    console.print("\n📡 [bold yellow]Host address configuration[/bold yellow]")
    console.print("🔍 [dim]Host address determines the network interface the service listens on:[/dim]")
    console.print("\n⚠️  [bold red]Security tips:[/bold red]")
    console.print("   When using 0.0.0.0, please ensure:")
    console.print("   1. Firewall rules are configured")
    console.print("   2. Running in a trusted network environment")
    
    host = questionary.select(
        "Select host address:",
        choices=[
            questionary.Choice("localhost (Only accessible from this machine)", "localhost"),
            questionary.Choice("0.0.0.0 (Allow external access)", "0.0.0.0")
        ],
        default="localhost"
    ).ask()
    
    public_read_url = ""
    
    if host == "0.0.0.0":
        console.print("⚠️  [bold yellow]External access is enabled, please ensure network security![/bold yellow]")
        
        # Configure PUBLIC_READ_URL for external access
        console.print("\n🌐 [bold yellow]Public URL configuration[/bold yellow]")
        console.print("🔍 [dim]When allowing external access, you need to configure the public URL for file access.[/dim]")
        
        # Try to detect local IP address
        try:
            # Connect to a remote address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            suggested_url = f"http://{local_ip}:{port}"
        except:
            local_ip = "YOUR_IP_ADDRESS"
            suggested_url = f"http://{local_ip}:{port}"
        
        console.print(f"🔍 [dim]Detected local IP: {local_ip}[/dim]")
        console.print(f"💡 [dim]Suggested public URL: {suggested_url}[/dim]")
        
        url_choice = questionary.select(
            "How would you like to configure the public URL?",
            choices=[
                questionary.Choice(f"Use detected IP ({suggested_url})", "auto"),
                questionary.Choice("Enter custom URL (domain/public IP)", "custom"),
                questionary.Choice("Skip for now (configure later)", "skip")
            ],
            default="auto"
        ).ask()
        
        if url_choice == "auto" and local_ip != "YOUR_IP_ADDRESS":
            public_read_url = suggested_url
            console.print(f"✅ Public URL set to: {public_read_url}")
        elif url_choice == "custom":
            public_read_url = questionary.text(
                "Enter public URL (e.g., http://your-domain.com:9004 or http://your-public-ip:9004):",
                instruction="Include protocol (http/https) and port if needed"
            ).ask()
            if public_read_url:
                console.print(f"✅ Public URL set to: {public_read_url}")
        else:
            console.print("⏭️  Public URL skipped, you can configure it later in the .env file")
    else:
        console.print(f"✅ Service will listen on {host}")
    
    return {
        "port": port,
        "host": host,
        "public_read_url": public_read_url,
    }
