# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
Middleware package for Pixelle MCP.
"""

from .static_cache_middleware import StaticCacheMiddleware
from .html_cdn_replace_middleware import HTMLCDNReplaceMiddleware
from .app_js_middleware import AppJsMiddleware

__all__ = ['StaticCacheMiddleware', 'HTMLCDNReplaceMiddleware', 'AppJsMiddleware']
