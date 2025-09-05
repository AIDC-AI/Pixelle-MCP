# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from enum import Enum
from typing import Tuple, Literal
from PIL import Image
from utils.file_util import download_files


class AspectRatio(Enum):
    """Enumeration of image aspect ratios"""
    SQUARE = "1:1"           # 1:1 Square
    LANDSCAPE_16_9 = "16:9"  # 16:9 Horizontal
    PORTRAIT_9_16 = "9:16"   # 9:16 Vertical
    LANDSCAPE_4_3 = "4:3"    # 4:3 Horizontal
    PORTRAIT_3_4 = "3:4"     # 3:4 Vertical
    
    @property
    def ratio_value(self) -> float:
        """Get the value of the aspect ratio"""
        if self == AspectRatio.SQUARE:
            return 1.0
        elif self == AspectRatio.LANDSCAPE_16_9:
            return 16/9
        elif self == AspectRatio.PORTRAIT_9_16:
            return 9/16
        elif self == AspectRatio.LANDSCAPE_4_3:
            return 4/3
        elif self == AspectRatio.PORTRAIT_3_4:
            return 3/4
        return 1.0
    
    def get_dimensions(self, quality: Literal["low", "high"] = "low") -> Tuple[int, int]:
        """
        Get the specific width and height based on the aspect ratio and quality
        
        Args:
            quality: "low" or "high"
            
        Returns:
            Tuple[int, int]: (width, height)
        """
        if quality == "high":
            long_side = 1024
        else:  # low quality
            long_side = 512
            
        if self in [AspectRatio.LANDSCAPE_16_9, AspectRatio.LANDSCAPE_4_3]:
            # Horizontal, width is the long side
            width = long_side
            height = int(long_side / self.ratio_value)
        elif self in [AspectRatio.PORTRAIT_9_16, AspectRatio.PORTRAIT_3_4]:
            # Vertical, height is the long side
            height = long_side
            width = int(long_side * self.ratio_value)
        else:  # Square
            width = height = long_side
            
        return width, height


async def detect_image_aspect_ratio_enum(image_url: str) -> AspectRatio:
    """
    Detect the aspect ratio of the image from the image URL
    
    Args:
        image_url: The URL of the image
        
    Returns:
        AspectRatio: Aspect ratio enumeration
    """
    try:
        async with download_files(image_url) as temp_file_path:
            with Image.open(temp_file_path) as img:
                width, height = img.size
                
                # Calculate the aspect ratio
                ratio = width / height
                
                # Return the corresponding aspect ratio enumeration based on the ratio
                if abs(ratio - 1.0) < 0.1:  # Close to square
                    return AspectRatio.SQUARE
                elif abs(ratio - 16/9) < 0.1:  # Close to 16:9
                    return AspectRatio.LANDSCAPE_16_9
                elif abs(ratio - 9/16) < 0.1:  # Close to 9:16
                    return AspectRatio.PORTRAIT_9_16
                elif abs(ratio - 4/3) < 0.1:  # Close to 4:3
                    return AspectRatio.LANDSCAPE_4_3
                elif abs(ratio - 3/4) < 0.1:  # Close to 3:4
                    return AspectRatio.PORTRAIT_3_4
                else:
                    # Determine whether it is horizontal or vertical based on the aspect ratio
                    if ratio > 1:
                        return AspectRatio.LANDSCAPE_16_9  # Default horizontal aspect ratio
                    else:
                        return AspectRatio.PORTRAIT_9_16  # Default vertical aspect ratio
                        
    except Exception as e:
        # If detection fails, return the default value
        return AspectRatio.SQUARE


async def detect_image_aspect_ratio(image_url: str) -> str:
    """
    Detect the aspect ratio of the image from the image URL (backward compatible function)
    
    Args:
        image_url: The URL of the image
        
    Returns:
        str: Aspect ratio string, such as "1:1", "16:9", "9:16", "4:3", "3:4"
    """
    aspect_ratio_enum = await detect_image_aspect_ratio_enum(image_url)
    return aspect_ratio_enum.value 