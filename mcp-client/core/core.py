# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from yml_env_loader import load_yml_and_set_env
import logging

# load config.yml and inject environment variables
load_yml_and_set_env("client")

# log config
logger_level = logging.INFO
logging.basicConfig(
    level=logger_level,
    format='%(asctime)s- %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

logger = logging.getLogger("PMC")
logger.setLevel(logger_level)

logging.getLogger("httpx").setLevel(logging.WARNING)
