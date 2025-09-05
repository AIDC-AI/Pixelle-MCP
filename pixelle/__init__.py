# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""Pixelle MCP package."""

import tomllib
from pathlib import Path

def get_version() -> str:
    """Get the version from multiple sources"""
    # Method 1: Try to get version from installed package metadata (works for uvx/pip)
    try:
        from importlib.metadata import version
        return version("pixelle")
    except Exception:
        pass
    
    # Method 2: Try to get version from pyproject.toml (works for development)
    try:
        # Find the pyproject.toml file in multiple possible locations
        current_dir = Path(__file__).parent
        possible_paths = [
            # For development environment (project root)
            current_dir.parent / "pyproject.toml",
            # For installed package (included in package)
            current_dir / "pyproject.toml",
            # For uvx/pip installed package (in site-packages)
            current_dir / ".." / "pyproject.toml",
        ]
        
        pyproject_path = None
        for path in possible_paths:
            if path.exists():
                pyproject_path = path
                break
        
        if pyproject_path is None:
            return "unknown"
            
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
            
        return pyproject_data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"

__version__ = get_version()
