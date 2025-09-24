# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import chainlit as cl
from chainlit.mcp import McpConnection
from mcp import ClientSession
import pixelle.web.utils.llm_util as llm_util
from pixelle.web.converters.message_converter import messages_from_chaintlit_to_openai
import pixelle.web.chat.starters as starters

from pixelle.logger import logger
from pixelle.web.core.prompt import DEFAULT_SYSTEM_PROMPT
from pixelle.web.converters.tool_converter import tools_from_chaintlit_to_openai
from pixelle.utils.user_settings_util import get_system_prompt
from pixelle.web.chat.chat_handler import handle_mcp_connect, handle_mcp_disconnect
from pixelle.web.chat.chat_settings import setup_chat_settings, setup_settings_update
from pixelle.web.chat import chat_handler as tool_handler
from pixelle.web import auth
from pixelle.utils.file_uploader import upload


@cl.set_chat_profiles
async def chat_profile(user: cl.User | None) -> list[cl.ChatProfile]:
    models = llm_util.get_all_models()
    default_model = llm_util.get_default_model()
    default_model_name = default_model.name if default_model else None
    return [
        cl.ChatProfile(
            name=model.name,
            markdown_description=f"Use **{model.name}** to talk with you.",
            default=default_model_name == model.name,
        )
        for model in models
    ]

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    await setup_chat_settings()
    
    # Get system prompt from file first, then from settings, finally use default value
    saved_system_prompt = get_system_prompt()
    settings = cl.user_session.get("settings", {})
    system_prompt = saved_system_prompt or settings.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    
    sys_message = cl.Message(
        type="system_message",
        content=system_prompt
    )
    cl.chat_context.add(sys_message)
    
@cl.on_settings_update
async def on_settings_update(settings):
    await setup_settings_update(settings)

@cl.on_mcp_connect
async def on_mcp(connection: McpConnection, session: ClientSession) -> None:
    """Handle MCP connection"""
    await handle_mcp_connect(connection, session, tools_from_chaintlit_to_openai)
    cl.user_session.set("mcp_session", session)


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """Called when MCP connection is disconnected"""
    logger.info(f"MCP connection is disconnected: {name}")
    await handle_mcp_disconnect(name)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user message"""
    # Check if it is a starter message, if it is handled, return directly
    is_handled = await starters.hook_by_starters(message)
    if is_handled:
        return
    
    need_update = False
    for element in message.elements:
        is_media = isinstance(element, cl.Image) \
            or isinstance(element, cl.Audio) \
            or isinstance(element, cl.Video)
        if is_media and element.path and not element.url:
            element.size = "small"
            element.url = upload(element.path, filename=element.name)
            need_update = True
    if need_update:
        await message.update()
    
    cl_messages = cl.chat_context.get()
    messages = messages_from_chaintlit_to_openai(cl_messages)
    
    # Use tool processor to process streaming response and tool calls
    chat_profile = cl.user_session.get("chat_profile")
    model_info = llm_util.get_model_info_by_name(chat_profile)
    await tool_handler.process_streaming_response(
        messages=messages,
        model_info=model_info,
    )


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
