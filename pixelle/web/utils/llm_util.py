# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from enum import Enum
from typing import Union, Optional

from pydantic import BaseModel, Field

from pixelle.logger import logger
from pixelle.settings import settings

# default model
CHAINLIT_CHAT_DEFAULT_MODEL = settings.chainlit_chat_default_model
logger.info(f"Default chat model: {CHAINLIT_CHAT_DEFAULT_MODEL}")


# OpenAI config
OPENAI_BASE_URL = settings.openai_base_url
OPENAI_API_KEY = settings.openai_api_key
CHAINLIT_CHAT_OPENAI_MODELS = settings.chainlit_chat_openai_models
openai_models = [model.strip() for model in CHAINLIT_CHAT_OPENAI_MODELS.split(",") if model.strip()]
if openai_models and not OPENAI_API_KEY:
    openai_models.clear()
    logger.warning("No OpenAI API key found, ignore OpenAI models, you can set `OPENAI_API_KEY` in `.env` to enable OpenAI models")
logger.info(f"OPENAI_BASE_URL: {OPENAI_BASE_URL}")
logger.info(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
logger.info(f"Found {len(openai_models)} OpenAI models: {openai_models}")


# Ollama config
OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_MODELS = settings.ollama_models
OLLAMA_API_KEY = "ollama"
ollama_models = [model.strip() for model in OLLAMA_MODELS.split(",") if model.strip()]
if ollama_models and not OLLAMA_BASE_URL:
    ollama_models.clear()
    logger.warning("No Ollama base URL found, ignore Ollama models, you can set `OLLAMA_BASE_URL` in `.env` to enable Ollama models")
logger.info(f"OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
logger.info(f"Found {len(ollama_models)} Ollama models: {ollama_models}")


# Gemini config
GEMINI_BASE_URL = settings.gemini_base_url
GEMINI_API_KEY = settings.gemini_api_key
GEMINI_MODELS = settings.gemini_models
gemini_models = [model.strip() for model in GEMINI_MODELS.split(",") if model.strip()]
if gemini_models and not GEMINI_API_KEY:
    gemini_models.clear()
    logger.warning("No Gemini API key found, ignore Gemini models, you can set `GEMINI_API_KEY` in `.env` to enable Gemini models")
logger.info(f"GEMINI_BASE_URL: {GEMINI_BASE_URL}")
logger.info(f"GEMINI_API_KEY: {GEMINI_API_KEY}")
logger.info(f"Found {len(gemini_models)} Gemini models: {gemini_models}")


# DeepSeek config
DEEPSEEK_BASE_URL = settings.deepseek_base_url
DEEPSEEK_API_KEY = settings.deepseek_api_key
DEEPSEEK_MODELS = settings.deepseek_models
deepseek_models = [model.strip() for model in DEEPSEEK_MODELS.split(",") if model.strip()]
if deepseek_models and not DEEPSEEK_API_KEY:
    deepseek_models.clear()
    logger.warning("No DeepSeek API key found, ignore DeepSeek models, you can set `DEEPSEEK_API_KEY` in `.env` to enable DeepSeek models")
logger.info(f"DEEPSEEK_BASE_URL: {DEEPSEEK_BASE_URL}")
logger.info(f"DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY}")
logger.info(f"Found {len(deepseek_models)} DeepSeek models: {deepseek_models}")


# Claude config
CLAUDE_BASE_URL = settings.claude_base_url
CLAUDE_API_KEY = settings.claude_api_key
CLAUDE_MODELS = settings.claude_models
claude_models = [model.strip() for model in CLAUDE_MODELS.split(",") if model.strip()]
if claude_models and not CLAUDE_API_KEY:
    claude_models.clear()
    logger.warning("No Claude API key found, ignore Claude models, you can set `CLAUDE_API_KEY` in `.env` to enable Claude models")
logger.info(f"CLAUDE_BASE_URL: {CLAUDE_BASE_URL}")
logger.info(f"CLAUDE_API_KEY: {CLAUDE_API_KEY}")
logger.info(f"Found {len(claude_models)} Claude models: {claude_models}")


# Qwen config
QWEN_BASE_URL = settings.qwen_base_url
QWEN_API_KEY = settings.qwen_api_key
QWEN_MODELS = settings.qwen_models
qwen_models = [model.strip() for model in QWEN_MODELS.split(",") if model.strip()]
if qwen_models and not QWEN_API_KEY:
    qwen_models.clear()
    logger.warning("No Qwen API key found, ignore Qwen models, you can set `QWEN_API_KEY` in `.env` to enable Qwen models")
logger.info(f"QWEN_BASE_URL: {QWEN_BASE_URL}")
logger.info(f"QWEN_API_KEY: {QWEN_API_KEY}")
logger.info(f"Found {len(qwen_models)} Qwen models: {qwen_models}")


# At least one model should be configured
if not any([
    openai_models,
    ollama_models,
    gemini_models,
    deepseek_models,
    claude_models,
    qwen_models,
]):
    raise ValueError(
        "Configuration Error: No models configured; please set at least one model in `.env` "
        "(OpenAI, Ollama, Gemini, DeepSeek, Claude, or Qwen)."
    )



class ModelType(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    QWEN = "qwen"


class ModelInfo(BaseModel):
    type: ModelType = Field(description="The type of the model")
    name: str = Field(description="The model name")
    base_url: str = Field(description="The base URL of the model")
    api_key: str = Field(description="The API key of the model")
    
    # LiteLLM (internal use, user not aware)
    provider: Optional[str] = Field(default=None, description="LiteLLM provider")
    model: Optional[str] = Field(default=None, description="Actual model name for LiteLLM")
    

def get_openai_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.OPENAI,
            name=model,
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
            provider="openai",
            model=model
        )
        for model in openai_models
    ]

def get_ollama_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.OLLAMA,
            name=model,
            base_url=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY,
            provider="openai",
            model=model
        )
        for model in ollama_models
    ]

def get_gemini_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.GEMINI,
            name=model,
            base_url=GEMINI_BASE_URL,
            api_key=GEMINI_API_KEY,
            provider="openai",
            model=model
        )
        for model in gemini_models
    ]

def get_deepseek_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.DEEPSEEK,
            name=model,
            base_url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY,
            provider="deepseek",
            model=model
        )
        for model in deepseek_models
    ]

def get_claude_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.CLAUDE,
            name=model,
            base_url=CLAUDE_BASE_URL,
            api_key=CLAUDE_API_KEY,
            provider="anthropic",
            model=model
        )
        for model in claude_models
    ]

def get_qwen_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.QWEN,
            name=model,
            base_url=QWEN_BASE_URL,
            api_key=QWEN_API_KEY,
            provider="openai",
            model=model
        )
        for model in qwen_models
    ]

def get_all_models() -> list[ModelInfo]:
    return get_openai_models() + get_ollama_models() + get_gemini_models() + get_deepseek_models() + get_claude_models() + get_qwen_models()

def get_default_model() -> Union[ModelInfo, None]:
    for model_info in get_all_models():
        if model_info.name == CHAINLIT_CHAT_DEFAULT_MODEL:
            return model_info
    return None

def get_model_info_by_name(name: str | None) -> ModelInfo:
    if name:
        for model_info in get_all_models():
            if model_info.name == name:
                return model_info
    
    default_model = get_default_model()
    if default_model:
        return default_model

    raise ValueError(f"Model `{name}` not found")
