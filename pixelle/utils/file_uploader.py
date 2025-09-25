# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os
import requests
from pathlib import Path
from typing import Union, Optional, Tuple
from urllib.parse import urlparse
import uuid

from pixelle.logger import logger
from pixelle.settings import settings
from pixelle.utils.os_util import get_data_path

class LocalFileUploader:
    
    def __init__(self):
        self.storage_path = Path(get_data_path(settings.local_storage_path))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, data: Union[bytes, str, Path], filename: Optional[str] = None) -> str:
        """
        Upload local file to storage directory
        
        Args:
            data: file data, can be bytes, file path or URL
            filename: optional file name
            
        Returns:
            str: file access URL
        """
        try:
            # process different types of input
            file_content, file_name = self._process_input(data, filename)
            
            # generate file id, keep consistent with LocalStorage
            file_id = self._generate_file_id(file_name)
            file_path = self.storage_path / file_id
            
            # write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # generate file URL
            file_url = self._get_file_url(file_id)
            
            logger.info(f"File saved successfully: {file_url}")
            return file_url
            
        except Exception as e:
            logger.error(f"File save failed: {e}")
            raise Exception(f"File upload failed: {str(e)}")
    
    def _generate_file_id(self, filename: str) -> str:
        """generate file id, keep consistent with LocalStorage"""
        ext = Path(filename).suffix
        return f"{uuid.uuid4().hex}{ext}"
    
    def _get_file_url(self, file_id: str) -> str:
        """generate file access URL"""
        return f"{settings.get_read_url()}/files/{file_id}"
    
    def _process_input(self, data: Union[bytes, str, Path], filename: Optional[str] = None) -> Tuple[bytes, str]:
        """process different types of input data"""
        # generate UUID as base file name
        base_name = uuid.uuid4().hex
        
        if isinstance(data, bytes):
            # directly is bytes data
            if filename:
                _, ext = os.path.splitext(filename)
            else:
                ext = ".bin"
            
            file_content = data
            file_name = filename or f"{base_name}{ext}"
        
        elif isinstance(data, (str, Path)):
            data_str = str(data)
            
            # check if it is URL or file path
            if data_str.startswith(('http://', 'https://')):
                # it is URL, download content
                response = requests.get(data_str, timeout=30)
                response.raise_for_status()
                file_content = response.content
                
                # determine file name
                if filename:
                    file_name = filename
                else:
                    # get file name from URL path
                    parsed_url = urlparse(data_str)
                    url_filename = os.path.basename(parsed_url.path)
                    if url_filename and '.' in url_filename:
                        file_name = url_filename
                    else:
                        # try to get extension from response header
                        content_type = response.headers.get('Content-Type', '')
                        ext = self._get_ext_from_content_type(content_type)
                        file_name = f"{base_name}{ext}"
            else:
                # it is file path
                file_path = Path(data_str)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # determine file name
                file_name = filename or file_path.name
        
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
        
        return file_content, file_name
    
    def _get_content_type(self, filename: str) -> str:
        """get file MIME type"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"
    
    def _get_ext_from_content_type(self, content_type: str) -> str:
        """get file extension from Content-Type"""
        if not content_type:
            return ".bin"
        
        import mimetypes
        mime_type = content_type.split(';')[0].strip()
        ext = mimetypes.guess_extension(mime_type)
        
        # optimize some common extensions
        if ext:
            if mime_type == 'image/jpeg' and ext in ['.jpe', '.jpeg']:
                ext = '.jpg'
            elif mime_type == 'image/tiff' and ext == '.tiff':
                ext = '.tif'
            return ext
        else:
            return ".bin"


# create default uploader instance
default_uploader = LocalFileUploader()


def upload(data: Union[bytes, str, Path], filename: Optional[str] = None) -> str:
    """
    unified interface for uploading files
    
    Args:
        data: file data, can be bytes, file path or URL
        filename: optional file name
        
    Returns:
        str: file access URL
    """
    return default_uploader.upload(data, filename) 