# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from pydantic import Field
from PIL import Image

from pixelle.logger import logger
from pixelle.mcp_core import mcp
from pixelle.utils.file_uploader import upload
from pixelle.utils.file_util import download_files, create_temp_file

@mcp.tool
async def i_crop(
    image_url: str = Field(description="The URL of the image to crop"),
):
    """Crop the image to the center of the original."""
    # Download the image using a context manager
    async with download_files(image_url, '.jpg') as temp_image_path:
        # Open the image and process it
        with Image.open(temp_image_path) as img:
            # Get original image dimensions
            original_width, original_height = img.size
            
            # Calculate new dimensions (half of the original)
            new_width = original_width // 2
            new_height = original_height // 2
            
            # Calculate coordinates for center cropping
            left = (original_width - new_width) // 2
            top = (original_height - new_height) // 2
            right = left + new_width
            bottom = top + new_height
            
            # Perform cropping
            cropped_img = img.crop((left, top, right, bottom))
            
            # If the image is in RGBA mode, convert it to RGB for JPEG saving
            if cropped_img.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', cropped_img.size, (255, 255, 255))
                # Paste RGBA image onto white background using alpha channel as mask
                background.paste(cropped_img, mask=cropped_img.split()[-1])
                cropped_img = background
            elif cropped_img.mode != 'RGB':
                # Convert other modes to RGB as well
                cropped_img = cropped_img.convert('RGB')
        
        # Save the cropped image to a temporary file
        with create_temp_file('_cropped.jpg') as cropped_output_path:
            # Save the cropped image
            cropped_img.save(cropped_output_path, format='JPEG', quality=95)
            
            # Upload the processed image
            result_url = upload(cropped_output_path, 'cropped_image.jpg')
            
            logger.info(f"[crop] Original size: {original_width}x{original_height}")
            logger.info(f"[crop] Cropped size: {new_width}x{new_height}")
            logger.info(f"[crop] Result URL: {result_url}")

            return (
                f"Original size: {original_width}x{original_height}\n"
                f"Cropped size: {new_width}x{new_height}\n"
                f"Result URL: {result_url}"
            )
