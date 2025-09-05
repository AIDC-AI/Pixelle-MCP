# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
OpenAPI utilities for handling compatibility issues with FastAPI and Chainlit integration.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def create_custom_openapi_function(app: FastAPI):
    """
    Create a custom OpenAPI generation function that handles OAuth2PasswordBearerWithCookie compatibility issues.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        A custom OpenAPI generation function
    """
    def custom_openapi():
        """Fix OAuth2PasswordBearerWithCookie compatibility issue with FastAPI OpenAPI generation"""
        if app.openapi_schema:
            return app.openapi_schema
        
        try:
            # Try normal OpenAPI generation first
            openapi_schema = get_openapi(
                title=app.title,
                version=getattr(app, 'version', "0.1.0"),
                description=app.description,
                routes=app.routes,
            )
            app.openapi_schema = openapi_schema
            return app.openapi_schema
        except AttributeError as e:
            # Fallback: generate OpenAPI only for safe routes when OAuth2PasswordBearerWithCookie causes issues
            if "model" in str(e):
                # Only include /files routes in API docs (exclude /pixelle MCP routes)
                safe_routes = [r for r in app.routes 
                              if hasattr(r, 'path') and r.path.startswith('/files')]
                app.openapi_schema = get_openapi(
                    title=app.title,
                    version=getattr(app, 'version', "0.1.0"),
                    description=app.description,
                    routes=safe_routes,
                )
                return app.openapi_schema
            raise
    
    return custom_openapi
