# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from pydantic import Field
from pixelle.mcp_core import mcp
from pixelle.utils.file_uploader import upload
from pixelle.logger import logger

@mcp.tool
async def upload_file(
    local_file_path: str = Field(description="The local path of the file to upload."),
):
    """
    Uploads a local file to the storage and returns its access URL.
    """
    try:
        result_url = upload(local_file_path)
        logger.info(f"File uploaded successfully: {result_url}")
        return {
            "result_url":result_url
            }
    except Exception as e:
        logger.error(f"Failed to upload file '{local_file_path}': {e}")
        raise Exception(f"File upload failed: {str(e)}")
