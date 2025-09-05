# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
Storage backend abstract base class
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from dataclasses import dataclass


@dataclass
class FileInfo:
    """File information"""
    file_id: str
    filename: str
    content_type: str
    size: int
    url: str


class StorageBackend(ABC):
    """Storage backend abstract base class"""
    
    @abstractmethod
    async def upload(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: str
    ) -> FileInfo:
        """
        Upload file
        
        Args:
            file_data: File data stream
            filename: File name
            content_type: File MIME type
            
        Returns:
            FileInfo: File information
        """
        pass
    
    @abstractmethod
    async def download(self, file_id: str) -> Optional[bytes]:
        """
        Download file
        
        Args:
            file_id: File ID
            
        Returns:
            bytes: File content, return None if file not exists
        """
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """
        Delete file
        
        Args:
            file_id: File ID
            
        Returns:
            bool: Whether delete successfully
        """
        pass
    
    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """
        Check if file exists
        
        Args:
            file_id: File ID
            
        Returns:
            bool: Whether file exists
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """
        Get file information
        
        Args:
            file_id: File ID
            
        Returns:
            FileInfo: File information, return None if file not exists
        """
        pass 