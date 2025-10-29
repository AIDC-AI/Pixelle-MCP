# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os
from typing import List
from pydantic import Field
import ffmpeg

from pixelle.logger import logger
from pixelle.mcp_core import mcp
from pixelle.utils.file_uploader import upload
from pixelle.utils.file_util import download_files, create_temp_file, cleanup_temp_files


def _is_url(path: str) -> bool:
    """Check if the path is a URL"""
    return path.startswith(('http://', 'https://'))


@mcp.tool
async def v_merge(
    video_paths: List[str] = Field(
        description="List of video URLs or local file paths to merge in order. Supports mixing URLs and local paths."
    ),
):
    """
    Merge multiple videos into one.
    
    This tool concatenates multiple video files in the order provided.
    Supports both remote URLs and local file paths as input.
    """
    if not video_paths or len(video_paths) < 2:
        return "Error: At least 2 videos are required for merging"
    
    temp_files_to_cleanup = []
    local_video_paths = []
    
    try:
        # Process each video path: download if URL, use directly if local path
        for idx, path in enumerate(video_paths):
            if _is_url(path):
                logger.info(f"Downloading video {idx + 1}/{len(video_paths)} from URL: {path}")
                async with download_files(path, '.mp4', auto_cleanup=False) as temp_path:
                    local_video_paths.append(temp_path)
                    temp_files_to_cleanup.append(temp_path)
            else:
                # Local file path
                if not os.path.exists(path):
                    return f"Error: Local file not found: {path}"
                logger.info(f"Using local video {idx + 1}/{len(video_paths)}: {path}")
                local_video_paths.append(path)
        
        # Merge videos using ffmpeg-python
        logger.info(f"Merging {len(local_video_paths)} videos...")
        
        with create_temp_file('_merged.mp4') as output_path:
            # Create input streams
            inputs = [ffmpeg.input(video_path) for video_path in local_video_paths]
            
            # Extract video and audio streams from each input
            streams = []
            for inp in inputs:
                streams.append(inp.video)
                streams.append(inp.audio)
            
            # Concatenate videos (v=1 for video stream, a=1 for audio stream)
            joined = ffmpeg.concat(*streams, v=1, a=1).node
            video = joined[0]
            audio = joined[1]
            
            (
                ffmpeg
                .output(video, audio, output_path, vcodec='libx264', acodec='aac')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Videos merged successfully: {output_path}")
            
            # Upload the result
            result_url = upload(output_path)
            
            logger.info(f"[v_merge] Merged {len(video_paths)} videos")
            logger.info(f"[v_merge] Result URL: {result_url}")
            
            return (
                f"Successfully merged {len(video_paths)} videos\n"
                f"Result URL: {result_url}"
            )
            
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg error during video merge: {error_message}")
        return f"Error: Failed to merge videos - {error_message}"
    
    except Exception as e:
        logger.error(f"Failed to merge videos: {e}", exc_info=True)
        return f"Error: Failed to merge videos - {str(e)}"
    
    finally:
        # Cleanup downloaded temporary files
        if temp_files_to_cleanup:
            cleanup_temp_files(temp_files_to_cleanup)
            logger.debug(f"Cleaned up {len(temp_files_to_cleanup)} temporary video files")

