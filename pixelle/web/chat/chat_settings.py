# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, TextInput, Tags

from pixelle.logger import logger
from pixelle.web.core.prompt import DEFAULT_SYSTEM_PROMPT
from pixelle.utils.user_settings_util import get_system_prompt, save_system_prompt


async def setup_chat_settings():
    # Documentation: https://docs.chainlit.io/api-reference/chat-settings#usage
    
    # Load system prompt from file, fallback to default
    initial_prompt = get_system_prompt() or DEFAULT_SYSTEM_PROMPT
    
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="system_prompt",
                label="System Prompt",
                initial=initial_prompt,
                multiline=True,
                placeholder="Enter system prompt, which will guide the behavior and response of the AI assistant.",
            ),
        ]
    ).send()
    logger.debug(f"chat settings: {settings}")


async def setup_settings_update(settings):
    logger.debug(f"on_settings_update: {settings}")
    cl.user_session.set("settings", settings)
    
    # Save system prompt to file for persistence
    system_prompt = settings.get("system_prompt", "")
    if system_prompt and system_prompt.strip():
        save_system_prompt(system_prompt.strip())
        logger.info(f"Saved system prompt to file")
    else:
        # If user sets empty prompt, restore to default
        system_prompt = DEFAULT_SYSTEM_PROMPT
        save_system_prompt(system_prompt)
        logger.info(f"Restored system prompt to default value")
    
    await _update_system_prompt_if_need(system_prompt)

    
async def _update_system_prompt_if_need(system_prompt: str):
    cl_messages = cl.chat_context.get()
    if not cl_messages:
        return
    
    first_message = cl_messages[0]
    if first_message.type != "system_message":
        return
    
    first_message.content = system_prompt
    await first_message.update()
    logger.info(f"update system prompt: {system_prompt}")

