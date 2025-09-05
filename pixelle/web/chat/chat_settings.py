# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, TextInput, Tags

from pixelle.logger import logger
from pixelle.web.core.prompt import DEFAULT_SYSTEM_PROMPT


async def setup_chat_settings():
    # Documentation: https://docs.chainlit.io/api-reference/chat-settings#usage
    
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="system_prompt",
                label="System Prompt",
                initial=DEFAULT_SYSTEM_PROMPT,
                multiline=True,
                placeholder="Enter system prompt, which will guide the behavior and response of the AI assistant.",
            ),
        ]
    ).send()
    logger.debug(f"chat settings: {settings}")


async def setup_settings_update(settings):
    logger.debug(f"on_settings_update: {settings}")
    cl.user_session.set("settings", settings)
    
    await _update_system_prompt_if_need(settings)

    
async def _update_system_prompt_if_need(settings):
    cl_messages = cl.chat_context.get()
    if not cl_messages:
        return
    
    first_message = cl_messages[0]
    if first_message.type != "system_message":
        return
    
    first_message.content = settings.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    await first_message.update()
    logger.info(f"update system prompt: {first_message.content}")

