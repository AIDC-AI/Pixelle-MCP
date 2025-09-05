# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import mimetypes
from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException, UploadFile

from pixelle.upload.base import FileInfo
from pixelle.settings import settings
from pixelle.upload.local_storage import LocalStorage


class FileService:
    
    def __init__(self):
        self.storage = LocalStorage()
    
    def _get_content_type(self, filename: str) -> str:
        """Actual file MIME type"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"
    
    async def upload_file(self, file: UploadFile) -> FileInfo:
        """
        Upload file
        
        Args:
            file: uploaded file
            
        Returns:
            FileInfo: file info
        """
        
        # get file info
        filename = file.filename or "unknown"
        content_type = file.content_type or self._get_content_type(filename)
        
        try:
            # upload to storage backend
            file_info = await self.storage.upload(
                file_data=file.file,
                filename=filename,
                content_type=content_type
            )
            
            return file_info
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def get_file(self, file_id: str) -> Optional[bytes]:
        """
        Get file content
        
        Args:
            file_id: file ID
            
        Returns:
            bytes: file content, return None if file not exists
        """
        try:
            return await self.storage.download(file_id)
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return None
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """
        Get file info
        
        Args:
            file_id: file ID
            
        Returns:
            FileInfo: file info, return None if file not exists
        """
        try:
            return await self.storage.get_file_info(file_id)
        except Exception as e:
            print(f"Error getting file info {file_id}: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file
        
        Args:
            file_id: file ID
            
        Returns:
            bool: whether delete successfully
        """
        try:
            return await self.storage.delete(file_id)
        except Exception as e:
            print(f"Error deleting file {file_id}: {e}")
            return False
    
    async def file_exists(self, file_id: str) -> bool:
        """
        Check if file exists
        
        Args:
            file_id: file ID
            
        Returns:
            bool: whether file exists
        """
        try:
            return await self.storage.exists(file_id)
        except Exception as e:
            print(f"Error checking file existence {file_id}: {e}")
            return False


# global file service instance
file_service = FileService() 