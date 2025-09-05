# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from pixelle.upload.file_service import file_service
from pixelle.upload.base import FileInfo

# Create router
router = APIRouter(
    tags=["files"],
    responses={404: {"description": "Not found"}},
)


@router.post("/upload", response_model=FileInfo)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file
    
    Args:
        file: Uploaded file
        
    Returns:
        FileInfo: File information
    """
    return await file_service.upload_file(file)


@router.get("/{file_id}")
async def get_file(file_id: str):
    """
    Get file
    
    Args:
        file_id: File ID
        
    Returns:
        File content
    """
    # Get file information
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    # Get file content
    file_content = await file_service.get_file(file_id)
    if not file_content:
        raise HTTPException(status_code=404, detail="File content not found")

    # Return file stream
    return Response(
        content=file_content,
        media_type=file_info.content_type,
        headers={
            "Content-Disposition": f"inline; filename={file_info.filename}"
        }
    )


@router.get("/{file_id}/info", response_model=FileInfo)
async def get_file_info(file_id: str):
    """
    Get file information
    
    Args:
        file_id: File ID
        
    Returns:
        FileInfo: File information
    """
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return file_info


# Not open for now, to prevent data loss
# @router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete file
    
    Args:
        file_id: File ID
        
    Returns:
        Delete result
    """
    success = await file_service.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found or delete failed")
    return {"message": "File deleted successfully"}


@router.get("/{file_id}/exists")
async def check_file_exists(file_id: str):
    """
    Check if file exists
    
    Args:
        file_id: File ID
        
    Returns:
        Existence check result
    """
    exists = await file_service.file_exists(file_id)
    return {"exists": exists}
