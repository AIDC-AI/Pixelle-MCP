# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
from pathlib import Path
from typing import Dict, Any

from pixelle.utils.os_util import get_data_path
from pixelle.logger import logger


def get_user_settings_file_path() -> Path:
    """Get user settings file path"""
    data_path = get_data_path()
    return Path(data_path) / "user_settings.json"


def load_user_settings() -> Dict[str, Any]:
    """Load user settings from JSON file"""
    settings_file = get_user_settings_file_path()
    
    if not settings_file.exists():
        return {}
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        logger.debug(f"Loaded user settings from {settings_file}")
        return settings
    except Exception as e:
        logger.error(f"Failed to load user settings: {e}")
        return {}


def save_user_settings(settings: Dict[str, Any]) -> bool:
    """Save user settings to JSON file"""
    settings_file = get_user_settings_file_path()
    
    try:
        # Ensure data directory exists
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved user settings to {settings_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save user settings: {e}")
        return False


def get_system_prompt() -> str:
    """Get system prompt from user settings"""
    settings = load_user_settings()
    return settings.get("system_prompt", "")


def save_system_prompt(system_prompt: str) -> bool:
    """Save system prompt to user settings"""
    settings = load_user_settings()
    settings["system_prompt"] = system_prompt
    return save_user_settings(settings)
