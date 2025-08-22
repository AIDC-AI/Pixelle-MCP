# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from fastmcp import FastMCP
from yml_env_loader import load_yml_and_set_env
import logging

# load config.yml and inject environment variables
load_yml_and_set_env("server")

# initialize MCP server
mcp = FastMCP(
    name="pixelle-mcp",
    on_duplicate_tools="replace",
)

# log config
logger_level = logging.INFO
logging.basicConfig(
    level=logger_level,
    format='%(asctime)s- %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

logger = logging.getLogger("PMS")
logger.setLevel(logger_level)
