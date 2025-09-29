# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).
from typing import Optional
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from pathlib import Path

from pixelle.utils.os_util import get_pixelle_root_path, get_root_path, get_src_path


# Load .env file from root path
def load_env_from_root_path():
    """Load .env from Pixelle root path"""
    root_path = get_pixelle_root_path()
    env_path = Path(root_path) / ".env"
    if env_path.exists():
        load_dotenv(env_path)

# Only load once on module import
if not os.getenv('PIXELLE_ENV_LOADED'):
    load_env_from_root_path()
    os.environ['PIXELLE_ENV_LOADED'] = 'true'


class Settings(BaseSettings):
    # Base service configuration
    host: str = "localhost"
    port: int = 9004
    public_read_url: Optional[str] = None
    local_storage_path: str = "files"
    
    # ComfyUI integration configuration
    comfyui_base_url: str = "http://localhost:8188"
    comfyui_api_key: str = ""
    comfyui_cookies: str = ""
    comfyui_executor_type: str = "http"
    
    # RunningHub configuration
    runninghub_base_url: str = "https://www.runninghub.ai"
    runninghub_api_key: str = ""
    runninghub_timeout: int = 3600
    runninghub_retry_count: int = 0
    
    # Chainlit configuration
    chainlit_auth_secret: str = "changeme-generate-a-secure-secret-key"
    chainlit_auth_enabled: bool = True
    chainlit_save_starter_enabled: bool = False
    
    # CDN configuration
    # Options: "auto" (detect by language), "china" (always use China CDN), "global" (always use global CDN)
    cdn_strategy: str = "auto"
    
    # LLM model configuration
    # OpenAI
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    chainlit_chat_openai_models: str = "gpt-4o-mini"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_models: str = ""
    
    # Gemini
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_api_key: str = ""
    gemini_models: str = ""
    
    # DeepSeek
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: str = ""
    deepseek_models: str = ""
    
    # Claude
    claude_base_url: str = "https://api.anthropic.com"
    claude_api_key: str = ""
    claude_models: str = ""
    
    # Qwen
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_api_key: str = ""
    qwen_models: str = ""
    
    # Default model
    chainlit_chat_default_model: str = "gpt-4o-mini"
    
    def get_configured_llm_providers(self) -> list[str]:
        """Get list of configured LLM providers"""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.ollama_models:
            providers.append("ollama") 
        if self.gemini_api_key:
            providers.append("gemini")
        if self.deepseek_api_key:
            providers.append("deepseek")
        if self.claude_api_key:
            providers.append("claude")
        if self.qwen_api_key:
            providers.append("qwen")
        return providers
    
    def get_all_available_models(self) -> list[str]:
        """Get list of all available models"""
        models = []
        
        if self.openai_api_key and self.chainlit_chat_openai_models:
            models.extend([m.strip() for m in self.chainlit_chat_openai_models.split(",") if m.strip()])
        
        if self.ollama_models:
            models.extend([m.strip() for m in self.ollama_models.split(",") if m.strip()])
            
        if self.gemini_api_key and self.gemini_models:
            models.extend([m.strip() for m in self.gemini_models.split(",") if m.strip()])
            
        if self.deepseek_api_key and self.deepseek_models:
            models.extend([m.strip() for m in self.deepseek_models.split(",") if m.strip()])
            
        if self.claude_api_key and self.claude_models:
            models.extend([m.strip() for m in self.claude_models.split(",") if m.strip()])
            
        if self.qwen_api_key and self.qwen_models:
            models.extend([m.strip() for m in self.qwen_models.split(",") if m.strip()])
        
        return models

    def get_read_url(self) -> str:
        if self.public_read_url:
            return self.public_read_url
        return f"http://{self.host}:{self.port}"

    class Config:
        extra = "ignore"


# Global settings instance
settings = Settings()

# Extra env vars for Chainlit
# Set CHAINLIT_APP_ROOT to package source directory (where .chainlit/ is packaged)
os.environ["CHAINLIT_APP_ROOT"] = get_src_path()
os.environ["CHAINLIT_HOST"] = str(settings.host)
os.environ["CHAINLIT_PORT"] = str(settings.port)
