# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Configuration saving and loading utilities."""

from typing import Dict, List, Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from pixelle.utils.config_util import build_env_lines

console = Console()


def save_unified_config(comfyui_config: Optional[Dict], runninghub_config: Optional[Dict], 
                       llm_configs: List[Dict], service_config: Dict, default_model: Optional[str] = None):
    """Save unified configuration to .env file"""
    console.print(Panel(
        "💾 [bold]Save configuration[/bold]\n\n"
        "Saving configuration to .env file...",
        title="Step 4/4: Save configuration",
        border_style="magenta"
    ))
    
    env_lines = build_env_lines(comfyui_config, runninghub_config, llm_configs, service_config, default_model)
    
    # Save to root path
    from pixelle.utils.os_util import ensure_pixelle_root_path
    pixelle_root = ensure_pixelle_root_path()
    env_path = Path(pixelle_root) / '.env'
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_lines))
    
    console.print("✅ [bold green]Configuration saved to .env file[/bold green]")
    
    # Reload config immediately
    reload_config()


def reload_config():
    """Reload environment variables and settings configuration"""
    import os
    from dotenv import load_dotenv
    
    # Force reload .env file from root path
    from pixelle.utils.os_util import get_pixelle_root_path
    pixelle_root = get_pixelle_root_path()
    env_path = Path(pixelle_root) / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    
    # Set Chainlit environment variables
    from pixelle.utils.os_util import get_src_path
    import os
    os.environ["CHAINLIT_APP_ROOT"] = get_src_path()
    
    # Update global settings instance values
    from pixelle import settings as settings_module
    
    # Create new Settings instance to get latest configuration
    from pixelle.settings import Settings
    new_settings = Settings()
    
    # Update global settings object attributes
    for field_name in new_settings.model_fields:
        setattr(settings_module.settings, field_name, getattr(new_settings, field_name))
    
    console.print("🔄 [bold blue]Configuration reloaded[/bold blue]")
