# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ExecuteResult(BaseModel):
    """Execution result model"""
    status: str = Field(description="Execution status")
    prompt_id: Optional[str] = Field(None, description="Prompt ID")
    duration: Optional[float] = Field(None, description="Execution duration (in seconds)")
    images: List[str] = Field(default_factory=list, description="List of image URLs")
    images_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="Images grouped by variable name")
    audios: List[str] = Field(default_factory=list, description="List of audio URLs")
    audios_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="Audios grouped by variable name")
    videos: List[str] = Field(default_factory=list, description="List of video URLs")
    videos_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="Videos grouped by variable name")
    texts: List[str] = Field(default_factory=list, description="List of texts")
    texts_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="Texts grouped by variable name")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Raw outputs")
    msg: Optional[str] = Field(None, description="Message")
    
    def to_llm_result(self) -> str:
        """Convert to a result string readable by LLM"""
        if self.status == "completed":
            output = "Generated successfully"
            
            def format_media_output(media_type: str, media_list: List[str], by_var_dict: Dict[str, List[str]]) -> str:
                """Format media output"""
                if by_var_dict and len(by_var_dict) > 1:
                    var_dict = {k: v[0] if v else None for k, v in by_var_dict.items()}
                    return f", {media_type}: {var_dict}"
                else:
                    return f", {media_type}: {media_list}"
            
            # Process each type of media
            for media_type in ["images", "audios", "videos", "texts"]:
                media_list = getattr(self, media_type)
                by_var_dict = getattr(self, f"{media_type}_by_var")
                if media_list:
                    output += format_media_output(media_type, media_list, by_var_dict)
            
            return output
        else:
            result = f"Generation failed, status: {self.status}"
            if self.msg:
                result += f", message: {self.msg}"
            return result
