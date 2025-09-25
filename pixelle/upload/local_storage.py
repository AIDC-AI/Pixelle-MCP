# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import uuid
import aiofiles
from pathlib import Path
from typing import BinaryIO, Optional

from pixelle.upload.base import StorageBackend, FileInfo
from pixelle.settings import settings
from pixelle.utils.os_util import get_data_path


class LocalStorage(StorageBackend):

    def __init__(self, read_url: Optional[str] = None):
        self.storage_path = Path(get_data_path(settings.local_storage_path))
        self.read_url = read_url or settings.get_read_url()
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_id(self, filename: str) -> str:
        ext = Path(filename).suffix
        return f"{uuid.uuid4().hex}{ext}"
    
    def _get_file_path(self, file_id: str) -> Path:
        return self.storage_path / file_id
    
    def _get_file_url(self, file_id: str) -> str:
        return f"{self.read_url}/files/{file_id}"
    
    async def upload(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: str
    ) -> FileInfo:
        file_id = self._generate_file_id(filename)
        file_path = self._get_file_path(file_id)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = file_data.read()
            await f.write(content)
        
        file_size = len(content)
        
        return FileInfo(
            file_id=file_id,
            filename=filename,
            content_type=content_type,
            size=file_size,
            url=self._get_file_url(file_id)
        )
    
    async def download(self, file_id: str) -> Optional[bytes]:
        file_path = self._get_file_path(file_id)
        
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except Exception:
            return None
    
    async def delete(self, file_id: str) -> bool:
        file_path = self._get_file_path(file_id)
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    async def exists(self, file_id: str) -> bool:
        file_path = self._get_file_path(file_id)
        return file_path.exists()
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        file_path = self._get_file_path(file_id)
        
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(file_path))
            
            return FileInfo(
                file_id=file_id,
                filename=file_path.name,
                content_type=content_type or "application/octet-stream",
                size=stat.st_size,
                url=self._get_file_url(file_id)
            )
        except Exception:
            return None 