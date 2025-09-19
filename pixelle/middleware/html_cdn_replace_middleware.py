"""
Copyright (C) 2025 AIDC-AI
This project is licensed under the MIT License (SPDX-License-identifier: MIT).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
from starlette.requests import Request

from pixelle.logger import logger
from pixelle.settings import settings


class HTMLCDNReplaceMiddleware(BaseHTTPMiddleware):
    """
    HTML CDN Replace Middleware
    
    Intelligently replaces CDN links based on configuration and user language preferences.
    Mainly solves the problem of slow loading of KaTeX, Google Fonts and other resources in China.
    
    CDN Strategy (controlled by cdn_strategy setting):
    - "auto": Detect by Accept-Language header (Chinese users get China CDN)
    - "china": Always use China CDN mirrors
    - "global": Always use original global CDNs
    
    Supported CDN replacements:
    - jsdelivr.net -> unpkg.shop.jd.com (for KaTeX and other npm packages)
    - fonts.googleapis.com -> fonts.loli.net (for Google Fonts CSS)
    - fonts.gstatic.com -> gstatic.loli.net (for Google Fonts static files)
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        # CDN prefix replacements for China users
        self.cdn_prefix_replacements = {
            # jsdelivr CDN replacement
            'https://cdn.jsdelivr.net/npm': 'https://unpkg.shop.jd.com',
            
            # Google Fonts API replacement
            'https://fonts.googleapis.com': 'https://fonts.loli.net',
            
            # Google Fonts static files replacement
            'https://fonts.gstatic.com': 'https://gstatic.loli.net',
        }

    def _should_use_china_cdn(self, request: Request) -> bool:
        """
        Determine if China CDN should be used based on configuration and user preferences
        
        Args:
            request: HTTP request object
            
        Returns:
            bool: True if China CDN should be used, False for global CDN
        """
        # Check configuration setting
        cdn_strategy = settings.cdn_strategy.lower()
        
        if cdn_strategy == "china":
            logger.debug("Using China CDN (forced by configuration)")
            return True
        elif cdn_strategy == "global":
            logger.debug("Using global CDN (forced by configuration)")
            return False
        elif cdn_strategy == "auto":
            # Auto-detect based on Accept-Language header
            accept_lang = request.headers.get("accept-language", "").lower()
            is_chinese = "zh" in accept_lang
            logger.debug(f"Auto-detect CDN: Accept-Language='{accept_lang}', using {'China' if is_chinese else 'global'} CDN")
            return is_chinese
        else:
            logger.warning(f"Unknown cdn_strategy: {cdn_strategy}, defaulting to global CDN")
            return False

    async def dispatch(self, request: Request, call_next):
        """
        Process request and replace CDN links in HTML response
        """
        response = await call_next(request)
        
        # Only process HTML responses
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("text/html"):
            return response
        
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            if not body:
                return response
            
            # Decode HTML content
            html_content = body.decode('utf-8')
            original_content = html_content
            
            # Determine if China CDN should be used
            use_china_cdn = self._should_use_china_cdn(request)
            
            if use_china_cdn:
                # Execute CDN prefix replacements for China users
                replacements_made = 0
                for original_prefix, replacement_prefix in self.cdn_prefix_replacements.items():
                    if original_prefix in html_content:
                        old_content = html_content
                        html_content = html_content.replace(original_prefix, replacement_prefix)
                        if html_content != old_content:
                            replacements_made += 1
                            logger.debug(f"HTML CDN prefix replaced: {original_prefix} -> {replacement_prefix}")
                
                if replacements_made > 0:
                    logger.info(f"Applied China CDN replacements: {replacements_made} replacements")
            else:
                logger.debug("Using original global CDNs (no replacement)")
            
            # If content changed, return new response
            if html_content != original_content:
                return Response(
                    content=html_content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="text/html"
                )
            
            # No content change, return original response
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            logger.warning(f"HTML CDN replace middleware error: {e}")
            # Return original response on error
            return response
