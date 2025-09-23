# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

# !!! Don't modify the import order, `settings` module must be imported before other modules !!!
from pixelle.settings import settings

from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
from chainlit.config import load_module, config as chainlit_config
from chainlit.server import lifespan as chainlit_lifespan
from chainlit.server import app as chainlit_app

from pixelle.utils.os_util import get_src_path
from pixelle.utils.openapi_util import create_custom_openapi_function
from pixelle.mcp_core import mcp
from pixelle.api.files_api import router as files_router
from pixelle.middleware import StaticCacheMiddleware, HTMLCDNReplaceMiddleware, AppJsMiddleware


# Modify chainlit config
chainlit_config.run.host = settings.host
chainlit_config.run.port = settings.port

# Access chainlit entry file path
chainlit_entry_file = get_src_path("web/app.py")
# Load chainlit module
load_module(chainlit_entry_file)

# Create ASGI app of MCP
mcp_app = mcp.http_app(path='/mcp')


# combine multi lifespans
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    # start MCP lifespan
    async with mcp_app.lifespan(app):
        # start chainlit lifespan
        async with chainlit_lifespan(app):
            yield


# Create a fastapi application
app = FastAPI(
    title="Pixelle-MCP",
    description="A fastapi app that contains mcp server and mcp client.",
    lifespan=combined_lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add HTML CDN replace middleware to fix slow CDN loading in China
# Problem: Chainlit uses jsdelivr.net CDN for KaTeX and fonts.googleapis.com for fonts, which are slow or blocked in China
# Solution: This middleware intercepts HTML responses and replaces CDN prefixes with China-accessible mirrors
app.add_middleware(HTMLCDNReplaceMiddleware)

# Add app.js middleware to always serve fresh content (for development)
app.add_middleware(AppJsMiddleware)

# Add static cache middleware to fix Chainlit's HTTP caching issues
# Problem: Chainlit/Uvicorn doesn't properly handle conditional HTTP requests (If-None-Match, If-Modified-Since)
# causing browsers to re-download large JS files even when they haven't changed, leading to slow performance
# after the server runs for a while.
# Solution: This middleware intercepts static file requests and implements proper HTTP caching protocol.
# Add static cache middleware for hashed static files (long cache)
app.add_middleware(
    StaticCacheMiddleware,
    static_paths=['/assets/', '/static/', '/_next/static/'],
    max_age=31536000,  # 1 year cache - files have content hashes in names, safe for long cache
)


# Load tools modules manually (avoid loading residual files from old installations)
from pixelle.tools import i_crop
from pixelle.tools import workflow_manager_tool

# Register files router
app.include_router(files_router, prefix="/files")

# Mount MCP server to `/pixelle` path
app.mount("/pixelle", mcp_app)

# Transfer all middleware into our app
for middleware in chainlit_app.user_middleware:
    app.add_middleware(middleware.cls, **middleware.kwargs)

# Copy all routes that are in Chainlit's app into our app, excluding duplicates
fastapi_standard_paths = {'/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc'}
for route in chainlit_app.routes:
    # Skip routes that would conflict with FastAPI's standard documentation routes
    if hasattr(route, 'path') and route.path in fastapi_standard_paths:
        continue
    app.router.routes.append(route)


# Override the default OpenAPI generation with custom function
app.openapi = create_custom_openapi_function(app)


def main():
    import uvicorn
    print("🚀 Start server...")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
