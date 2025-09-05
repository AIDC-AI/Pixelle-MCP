# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).
import importlib
from pathlib import Path
from pixelle.logger import logger
import pixelle

def load_modules(module_name: str, src_dir:str="pixelle"):
    base_path = Path(pixelle.__file__).parent
    module_dir = base_path / module_name
    logger.info(f"Loading modules from {module_dir.absolute()}...")

    if not module_dir.exists():
        logger.error(f"{module_name} directory not found!")
        return

    for py_file in module_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        module_name_with_ext = f"{src_dir}.{module_name}.{py_file.stem}"
        try:
            importlib.import_module(module_name_with_ext)
            logger.info(f"Loaded module from {module_name_with_ext}.")
        except Exception as e:
            logger.error(f"Error loading {module_name_with_ext} from {module_name}: {e}")
            raise  e
