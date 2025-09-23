# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
App.js middleware for development - always serve fresh content for /public/app.js
"""

from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_404_NOT_FOUND

from pixelle.logger import logger
from pixelle.utils.os_util import get_src_path


class AppJsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to always serve fresh /public/app.js content without caching.
    Perfect for development when you need immediate file updates.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Get the path to the app.js file
        self.app_js_path = Path(get_src_path("public/app.js"))
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and handle /public/app.js specially.
        """
        # Check if this is a request for /public/app.js
        if request.url.path == "/public/app.js" and request.method == "GET":
            return await self._serve_app_js(request)
        
        # For all other requests, continue with normal processing
        return await call_next(request)
    
    async def _serve_app_js(self, request: Request) -> Response:
        """
        Serve the app.js file with fresh content and no-cache headers.
        """
        try:
            if not self.app_js_path.exists():
                logger.warning(f"app.js file not found: {self.app_js_path}")
                return Response(
                    content="// app.js file not found",
                    status_code=HTTP_404_NOT_FOUND,
                    media_type="application/javascript"
                )
            
            # Read the file content fresh every time
            content = self.app_js_path.read_text(encoding='utf-8')
            
            # Create response with no-cache headers
            response = Response(
                content=content,
                media_type="application/javascript",
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                }
            )
            
            logger.debug(f"Served fresh app.js content from: {self.app_js_path}")
            return response
            
        except Exception as e:
            logger.error(f"Error serving app.js: {e}")
            return Response(
                content=f"// Error loading app.js: {e}",
                status_code=500,
                media_type="application/javascript"
            )
