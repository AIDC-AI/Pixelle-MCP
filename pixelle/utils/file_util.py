# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import requests
import tempfile
import os
import mimetypes
import aiohttp
import asyncio
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, List, Union, overload, AsyncGenerator
from urllib.parse import urlparse
from pixelle.logger import logger
from pixelle.utils.os_util import get_data_path


TEMP_DIR = get_data_path("temp")
os.makedirs(TEMP_DIR, exist_ok=True)


@overload
async def download_files(file_urls: str, suffix: str = None, auto_cleanup: bool = True, cookies: dict = None) -> AsyncGenerator[str, None]:
    ...


@overload
async def download_files(file_urls: List[str], suffix: str = None, auto_cleanup: bool = True, cookies: dict = None) -> AsyncGenerator[List[str], None]:
    ...


@asynccontextmanager
async def download_files(file_urls: Union[str, List[str]], suffix: str = None, auto_cleanup: bool = True, cookies: dict = None) -> AsyncGenerator[Union[str, List[str]], None]:
    """
    Download files from URLs to temporary files.
    
    Args:
        file_urls: Single URL string or URL list
        suffix: Temporary file suffix, if not specified, try to infer from URL
        auto_cleanup: Whether to automatically clean up temporary files, default is True
        cookies: Cookies used when requesting
        
    Yields:
        str: If input is str, return temporary file path
        List[str]: If input is List[str], return temporary file path list
        
    Automatically clean up all temporary files
    """
    is_single_url = isinstance(file_urls, str)
    url_list = [file_urls] if is_single_url else file_urls
    
    temp_file_paths = []
    try:
        for url in url_list:
            logger.info(f"Downloading file from URL: {url}")
            
            # Check if it is a local file service URL
            parsed_url = urlparse(url)
            is_local_file = await _is_local_file_url(url)
            
            if is_local_file:
                # Get file content directly from local file service
                file_content, content_type = await _get_local_file_content(url)
            else:
                # Download external file using asynchronous HTTP client
                file_content, content_type = await _download_external_file(url, cookies)
            
            # Determine file suffix
            file_suffix = suffix
            if not file_suffix:
                # Try to infer suffix from URL
                filename = os.path.basename(parsed_url.path)
                if filename and '.' in filename:
                    file_suffix = '.' + filename.split('.')[-1]
                else:
                    # If the extension cannot be obtained from the URL path, try to get it from the response header
                    file_suffix = get_ext_from_content_type(content_type or '')
                    if not file_suffix:
                        file_suffix = '.tmp'  # Default suffix
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix, dir=TEMP_DIR) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file_paths.append(temp_file.name)
        
        logger.info(f"Downloaded {len(temp_file_paths)} files to temporary files")
        
        # Return corresponding type based on input type
        if is_single_url:
            yield temp_file_paths[0]
        else:
            yield temp_file_paths
        
    except (requests.RequestException, aiohttp.ClientError) as e:
        logger.error(f"Download file failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error occurred while processing files: {str(e)}")
        raise
    finally:
        if auto_cleanup:
            cleanup_temp_files(temp_file_paths)


@contextmanager
def create_temp_file(suffix: str = '.tmp') -> Generator[str, None, None]:
    """
    Create a context manager for a temporary file.
    
    Args:
        suffix: Temporary file suffix
        
    Yields:
        str: Temporary file path
        
    Automatically clean up temporary files
    """
    temp_file_path = None
    try:        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_DIR) as temp_file:
            temp_file_path = temp_file.name
        
        logger.debug(f"Created temporary file: {temp_file_path}")
        yield temp_file_path
        
    finally:
        if temp_file_path:
            cleanup_temp_files(temp_file_path)


def get_ext_from_content_type(content_type: str) -> str:
    """Get file extension from Content-Type response header"""
    if not content_type:
        return ""
    
    # Parse Content-Type, remove parameters
    mime_type = content_type.split(';')[0].strip()
    
    # Use standard library's mimetypes.guess_extension
    ext = mimetypes.guess_extension(mime_type)
    
    # Optimize some common extensions (mimetypes sometimes returns uncommon ones)
    if ext:
        # Optimize JPEG extension
        if mime_type == 'image/jpeg' and ext in ['.jpe', '.jpeg']:
            ext = '.jpg'
        # Optimize TIFF extension  
        elif mime_type == 'image/tiff' and ext == '.tiff':
            ext = '.tif'
        
        logger.debug(f"Get extension from Content-Type '{content_type}': {ext}")
        return ext
    else:
        logger.debug(f"Unknown Content-Type: {content_type}")
        return ""


async def _is_local_file_url(url: str) -> bool:
    """Check if it is a local file service URL"""
    from pixelle.settings import settings
    local_base_url = f"http://{settings.host}:{settings.port}"
    return url.startswith(local_base_url) and "/files/" in url


async def _get_local_file_content(url: str) -> tuple[bytes, str]:
    """Get file content directly from local file service, avoid HTTP request loop"""
    from pixelle.upload.file_service import file_service
    
    # Extract file ID from URL
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'files':
        file_id = path_parts[1]
        
        # Get file content and information directly from file service
        file_content = await file_service.get_file(file_id)
        file_info = await file_service.get_file_info(file_id)
        
        if file_content is None:
            raise Exception(f"File not found: {file_id}")
            
        content_type = file_info.content_type if file_info else "application/octet-stream"
        return file_content, content_type
    
    raise Exception(f"Invalid local file URL: {url}")


async def _download_external_file(url: str, cookies: dict = None) -> tuple[bytes, str]:
    """Download external file using asynchronous HTTP client"""
    async with aiohttp.ClientSession(cookies=cookies, timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()
            content_type = response.headers.get('Content-Type', '')
            return content, content_type


def cleanup_temp_files(file_paths: Union[str, List[str]]) -> None:
    """
    Clean up temporary files.
    
    Args:
        file_paths: Single file path or file path list
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}") 