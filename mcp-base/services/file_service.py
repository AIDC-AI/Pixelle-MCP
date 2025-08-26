# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
文件服务
提供文件上传、下载、管理等功能
"""

import mimetypes
from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException, UploadFile

from storage import storage, FileInfo
from config.settings import settings


class FileService:
    """文件服务类"""
    
    def __init__(self):
        self.storage = storage
    
    def _validate_file(self, file: UploadFile) -> None:
        """验证上传的文件"""
        # 检查文件大小
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # 移动到文件末尾
            file_size = file.file.tell()
            file.file.seek(0)  # 重置到文件开头
            
            if file_size > settings.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
                )
    
    def _get_content_type(self, filename: str) -> str:
        """获取文件的MIME类型"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"
    
    async def upload_file(self, file: UploadFile) -> FileInfo:
        """
        上传文件
        
        Args:
            file: 上传的文件
            
        Returns:
            FileInfo: 文件信息
        """
        # 验证文件
        self._validate_file(file)
        
        # 获取文件信息
        filename = file.filename or "unknown"
        content_type = file.content_type or self._get_content_type(filename)
        
        try:
            # 上传到存储后端
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
        获取文件内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            bytes: 文件内容，如果文件不存在返回None
        """
        try:
            return await self.storage.download(file_id)
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return None
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            FileInfo: 文件信息，如果文件不存在返回None
        """
        try:
            return await self.storage.get_file_info(file_id)
        except Exception as e:
            print(f"Error getting file info {file_id}: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            return await self.storage.delete(file_id)
        except Exception as e:
            print(f"Error deleting file {file_id}: {e}")
            return False
    
    async def file_exists(self, file_id: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 文件是否存在
        """
        try:
            return await self.storage.exists(file_id)
        except Exception as e:
            print(f"Error checking file existence {file_id}: {e}")
            return False


# 全局文件服务实例
file_service = FileService() 
