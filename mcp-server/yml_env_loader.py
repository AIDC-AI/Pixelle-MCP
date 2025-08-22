# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os
import yaml
from pathlib import Path

def load_yml_and_set_env(service_key: str, config_filename: str = "config.yml"):
    """
    First load config.yml from current directory, then fallback to config.yml from project root directory.
    Only need to pass service_key (like base/server/client), automatically inject all configurations under that key to os.environ (variable names in uppercase).
    :param service_key: Service configuration key
    :param config_filename: Configuration filename, default config.yml
    """
    cwd = Path(__file__).parent.resolve()
    root = cwd.parent.resolve()

    config_paths = [cwd / config_filename, root / config_filename]
    loaded = False
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"[YML Config] Loading configuration file: {config_path.resolve()}")
            if not isinstance(config, dict):
                raise ValueError(f"YAML configuration format error: {config_path}")
            service_config = config.get(service_key, {})
            if not isinstance(service_config, dict):
                raise ValueError(f"Service {service_key} configuration format error: {config_path}")
            for k, v in service_config.items():
                os.environ[k.upper()] = str(v)
            loaded = True
            break
    if not loaded:
        raise FileNotFoundError(f"Configuration file {config_filename} not found, please provide configuration file in current directory or root directory") 