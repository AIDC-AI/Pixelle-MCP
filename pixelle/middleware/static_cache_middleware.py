# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
Static file cache middleware to fix HTTP caching issues with Chainlit's static file serving.
This middleware intercepts requests to static assets and implements proper HTTP caching protocol.
"""

import os
import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, FileResponse
from starlette.status import HTTP_304_NOT_MODIFIED, HTTP_404_NOT_FOUND

from pixelle.logger import logger


class StaticCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle static file caching properly.
    
    Fixes the issue where Chainlit/Uvicorn doesn't correctly handle conditional requests
    for static assets, causing browsers to re-download large files even when they haven't changed.
    """
    
    def __init__(self, app, static_paths: list[str] = None, max_age: int = 86400):
        """
        Initialize the static cache middleware.
        
        Args:
            app: The ASGI application
            static_paths: List of URL paths to intercept (default: ['/assets/', '/static/'])
            max_age: Cache max age in seconds (default: 24 hours)
        """
        super().__init__(app)
        self.static_paths = static_paths or ['/assets/', '/static/', '/_next/static/']
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and handle static file caching if applicable.
        """
        # Check if this is a request for a static file we should handle
        if not self._should_handle_request(request):
            return await call_next(request)
        
        try:
            # Try to handle as cached static file
            response = await self._handle_static_file(request)
            if response:
                # Log cache hits for monitoring
                if response.status_code == HTTP_304_NOT_MODIFIED:
                    logger.debug(f"Static cache HIT (304): {request.url.path}")
                else:
                    logger.debug(f"Static cache SERVE: {request.url.path}")
                return response
        except Exception as e:
            logger.warning(f"Static cache middleware error for {request.url.path}: {e}")
        
        # Fallback to original handling
        logger.debug(f"Static cache FALLBACK: {request.url.path}")
        return await call_next(request)
    
    def _should_handle_request(self, request: Request) -> bool:
        """
        Check if this request should be handled by the middleware.
        """
        path = request.url.path
        return (
            request.method == "GET" and
            any(path.startswith(static_path) for static_path in self.static_paths)
        )
    
    async def _handle_static_file(self, request: Request) -> Optional[Response]:
        """
        Handle static file request with proper caching.
        """
        file_path = await self._find_static_file(request.url.path)
        if not file_path or not file_path.exists():
            return None
        
        # Get file stats
        stat = file_path.stat()
        file_size = stat.st_size
        modified_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        
        # Generate ETag based on file path, size and modification time
        etag = self._generate_etag(file_path, file_size, modified_time)
        
        # Check conditional requests
        if_none_match = request.headers.get('if-none-match')
        if_modified_since = request.headers.get('if-modified-since')
        
        # Handle If-None-Match (ETag validation)
        if if_none_match:
            # Remove quotes if present
            client_etag = if_none_match.strip('"')
            if client_etag == etag.strip('"'):
                return self._create_304_response(etag, modified_time)
        
        # Handle If-Modified-Since
        if if_modified_since:
            try:
                client_time = datetime.strptime(
                    if_modified_since, '%a, %d %b %Y %H:%M:%S %Z'
                ).replace(tzinfo=timezone.utc)
                # Use integer seconds comparison to avoid microsecond differences
                if int(modified_time.timestamp()) <= int(client_time.timestamp()):
                    return self._create_304_response(etag, modified_time)
            except ValueError:
                # Invalid date format, ignore
                pass
        
        # Return file with proper cache headers
        return self._create_file_response(file_path, etag, modified_time)
    
    async def _find_static_file(self, url_path: str) -> Optional[Path]:
        """
        Find the actual file path for a static asset URL.
        """
        # Try to find Chainlit's static files in multiple possible locations
        search_paths = []
        
        try:
            import chainlit
            chainlit_package_dir = Path(chainlit.__file__).parent
            
            # Common Chainlit static directories
            possible_static_dirs = [
                chainlit_package_dir / "frontend" / "dist",
                chainlit_package_dir / "frontend" / "build", 
                chainlit_package_dir / "static",
                chainlit_package_dir / "public",
            ]
            
            search_paths.extend(possible_static_dirs)
            
        except Exception as e:
            logger.debug(f"Could not locate Chainlit package: {e}")
        
        # Also try common static directories
        search_paths.extend([
            Path.cwd() / "static",
            Path.cwd() / "public",
        ])
        
        # Search for the file in all possible locations
        for static_path in self.static_paths:
            if url_path.startswith(static_path):
                relative_path = url_path[len(static_path):]
                
                for search_dir in search_paths:
                    if search_dir.exists():
                        # Try direct mapping first (for /assets/ -> assets/)
                        file_path = search_dir / relative_path
                        if file_path.exists() and file_path.is_file():
                            logger.debug(f"Found static file: {file_path} for URL: {url_path}")
                            return file_path
                        
                        # Try with the static path prefix included (for /assets/ -> /assets/)
                        # This handles cases where the URL path matches the directory structure
                        full_relative_path = url_path.lstrip('/')
                        file_path = search_dir / full_relative_path
                        if file_path.exists() and file_path.is_file():
                            logger.debug(f"Found static file: {file_path} for URL: {url_path}")
                            return file_path
        
        logger.debug(f"Static file not found for URL: {url_path}")
        return None
    
    def _generate_etag(self, file_path: Path, file_size: int, modified_time: datetime) -> str:
        """
        Generate ETag for a file based on path, size, and modification time.
        """
        # Create a hash based on file path, size, and modification time
        content = f"{file_path}:{file_size}:{modified_time.timestamp()}"
        hash_object = hashlib.md5(content.encode())
        return f'"{hash_object.hexdigest()}"'
    
    def _create_304_response(self, etag: str, modified_time: datetime) -> Response:
        """
        Create a 304 Not Modified response.
        """
        headers = {
            'etag': etag,
            'last-modified': modified_time.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'cache-control': f'public, max-age={self.max_age}',
        }
        return Response(status_code=HTTP_304_NOT_MODIFIED, headers=headers)
    
    def _create_file_response(self, file_path: Path, etag: str, modified_time: datetime) -> FileResponse:
        """
        Create a file response with proper cache headers.
        """
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        
        # Create file response
        response = FileResponse(
            path=str(file_path),
            media_type=content_type,
            headers={
                'etag': etag,
                'last-modified': modified_time.strftime('%a, %d %b %Y %H:%M:%S GMT'),
                'cache-control': f'public, max-age={self.max_age}',
                'accept-ranges': 'bytes',
            }
        )
        
        return response
