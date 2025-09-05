# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from datetime import timedelta
import json
import os
import time
import chainlit as cl
from typing import Any, Dict, List
from mcp import ClientSession
import re
from pixelle.web.utils.llm_util import ModelInfo, ModelType

from litellm import acompletion

from pixelle.web.chat.starters import build_save_action
from pixelle.web.utils.time_util import format_duration
from pixelle.logger import logger
from pixelle.settings import settings

save_starter_enabled = settings.chainlit_save_starter_enabled


def format_llm_error_message(model_name: str, error_str: str) -> str:
    """Unified LLM error message formatting function"""
    # Handle common error types and provide friendly English error messages
    if "RateLimitError" in error_str or "429" in error_str:
        if "quota" in error_str.lower() or "exceed" in error_str.lower():
            return f"⚠️ {model_name} API quota exceeded. Please check your plan and billing details."
        else:
            return f"⚠️ {model_name} API rate limit hit. Please try again later."
    elif "401" in error_str or "authentication" in error_str.lower():
        return f"🔑 {model_name} API key is invalid. Please check your configuration."
    elif "403" in error_str or "permission" in error_str.lower():
        return f"🚫 {model_name} API access denied. Please check permissions."
    elif "timeout" in error_str.lower():
        return f"⏰ {model_name} API call timed out. Please retry."
    else:
        return f"❌ {model_name} model call failed: {error_str}"


def get_all_tools() -> List[Dict[str, Any]]:
    """Get all available MCP tools"""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    all_tools = []
    for connection_tools in mcp_tools.values():
        all_tools.extend(connection_tools)
    return all_tools


def find_tool_connection(tool_name: str) -> str:
    """Find the MCP connection that owns the tool"""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    for connection_name, tools in mcp_tools.items():
        if any(tool["function"]["name"] == tool_name for tool in tools):
            return connection_name
    return None


def _extract_content(content_list):
    """Extract text content from CallToolResult's content list"""
    if not content_list:
        return ""
    
    text_parts = []
    for content_item in content_list:
        # Handle different types of content
        if hasattr(content_item, 'text'):
            # TextContent
            text_parts.append(content_item.text)
        elif hasattr(content_item, 'data'):
            # ImageContent or other binary content
            text_parts.append(f"[Binary content: {getattr(content_item, 'mimeType', 'unknown')}]")
        elif hasattr(content_item, 'uri'):
            # EmbeddedResource
            text_parts.append(f"[Resource: {content_item.uri}]")
        else:
            # Other unknown types, try to convert to string
            text_parts.append(str(content_item))
    
    return text_parts[0] if len(text_parts) == 1 else text_parts


@cl.step(type="tool")
async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Execute MCP tool call"""
    # Record start time
    start_time = time.time()
    
    def _format_result_with_duration(content: str) -> str:
        """Unified formatting of results with duration"""
        duration = time.time() - start_time
        return f"[Took {format_duration(duration)}] {content}"
    
    current_step = cl.context.current_step
    current_step.input = tool_input
    current_step.name = tool_name
    await current_step.update()
    
    def record_step():
        # Get existing message history
        current_steps = cl.user_session.get("current_steps", [])
        current_steps.append(current_step)
        # Update message history
        cl.user_session.set("current_steps", current_steps)
    
    # Find the connection that owns the tool
    mcp_name = find_tool_connection(tool_name)
    if not mcp_name:
        error_msg = json.dumps({"error": f"Tool {tool_name} not found in any MCP connection"})
        result_with_duration = _format_result_with_duration(error_msg)
        current_step.output = result_with_duration
        record_step()
        return result_with_duration
    
    # Get MCP session
    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)
    if not mcp_session:
        error_msg = json.dumps({"error": f"MCP {mcp_name} not found in any MCP connection"})
        result_with_duration = _format_result_with_duration(error_msg)
        current_step.output = result_with_duration
        record_step()
        return result_with_duration
    
    try:
        # Call MCP tool, returns CallToolResult object
        logger.info(f"Calling MCP tool: {tool_name} with input: {tool_input}")
        result = await mcp_session.call_tool(tool_name, tool_input, read_timeout_seconds=timedelta(hours=1))
        
        # Check if there's an error
        if result.isError:
            error_content = _extract_content(result.content)
            logger.error(f"Tool execution failed: {error_content}")
            error_msg = json.dumps({"error": f"Tool execution failed: {error_content}"})
            result_with_duration = _format_result_with_duration(error_msg)
            current_step.output = result_with_duration
            return result_with_duration
        
        # Extract content text
        content = _extract_content(result.content)
        logger.info(f"Tool execution succeeded: {content}")
        result_with_duration = _format_result_with_duration(str(content))
        current_step.output = result_with_duration
        record_step()
        return result_with_duration
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        error_msg = json.dumps({"error": str(e)})
        result_with_duration = _format_result_with_duration(error_msg)
        current_step.output = result_with_duration
        record_step()
        return result_with_duration


def _extract_and_clean_media_markers(text: str) -> tuple[Dict[str, List[str]], str]:
    """Extract media markers and clean text
    
    Returns:
        tuple: (media files dict, cleaned text)
               media files dict format: {"images": [...], "audios": [...], "videos": [...]}
    """
    # Match different types of media markers
    patterns = {
        "images": r'\[SHOW_IMAGE:([^\]]+)\]',
        "audios": r'\[SHOW_AUDIO:([^\]]+)\]',
        "videos": r'\[SHOW_VIDEO:([^\]]+)\]'
    }
    
    media_files = {"images": [], "audios": [], "videos": []}
    cleaned_text = text
    
    # Extract various types of media files and clean text
    for media_type, pattern in patterns.items():
        media_files[media_type] = re.findall(pattern, cleaned_text)
        cleaned_text = re.sub(pattern, '', cleaned_text)
    
    # Remove extra whitespace
    cleaned_text = cleaned_text.rstrip()
    
    return media_files, cleaned_text


def _is_url(source: str) -> bool:
    """Check if media source is a URL"""
    return source.startswith(('http://', 'https://'))


async def _process_media_markers(msg: cl.Message):
    """Process media markers in messages"""
    if not msg.content:
        return
        
    # Extract media markers and clean text
    media_files, cleaned_content = _extract_and_clean_media_markers(msg.content)
    
    # If content becomes empty after removing media markers but we have media files,
    # set a default message to ensure the message with media elements is displayed
    has_media = any(media_files.values())
    if not cleaned_content.strip() and has_media:
        cleaned_content = "📎"  # Simple media indicator
    
    # Update message content (remove markers)
    msg.content = cleaned_content
    
    # Process images
    for i, img_source in enumerate(media_files["images"]):
        img_source = img_source.strip()
        
        img_params = {
            "name": f"Generated_Image_{i+1}",
            "display": "inline",
            "size": "small",
        }
        
        if _is_url(img_source):
            img_params["url"] = img_source
        else:
            img_params["path"] = img_source
        
        img_element = cl.Image(**img_params)
        msg.elements.append(img_element)
        logger.info(f"Added image element: {img_source}")
    
    # Process audio
    for i, audio_source in enumerate(media_files["audios"]):
        audio_source = audio_source.strip()
        
        audio_params = {
            "name": f"Generated_Audio_{i+1}",
            "display": "inline",
            "size": "small",
        }
        
        if _is_url(audio_source):
            audio_params["url"] = audio_source
        else:
            audio_params["path"] = audio_source
        
        audio_element = cl.Audio(**audio_params)
        msg.elements.append(audio_element)
        logger.info(f"Added audio element: {audio_source}")
    
    # Process video
    for i, video_source in enumerate(media_files["videos"]):
        video_source = video_source.strip()
        
        video_params = {
            "name": f"Generated_Video_{i+1}",
            "display": "inline",
            "size": "small",
        }
        
        if _is_url(video_source):
            video_params["url"] = video_source
        else:
            video_params["path"] = video_source
        
        video_element = cl.Video(**video_params)
        msg.elements.append(video_element)
        logger.info(f"Added video element: {video_source}")


async def _process_tool_call_delta(
    tool_calls_delta: List[Any], 
    current_tool_calls: Dict[int, Dict], 
    current_args: Dict[int, str]
):
    """Process incremental data for tool calls"""
    for tool_call_delta in tool_calls_delta:
        index = tool_call_delta.index
        
        # Initialize tool call data structure
        if index not in current_tool_calls:
            current_tool_calls[index] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""}
            }
            current_args[index] = ""
        
        # Accumulate tool call information
        if tool_call_delta.id:
            current_tool_calls[index]["id"] = tool_call_delta.id
        if tool_call_delta.function and tool_call_delta.function.name:
            current_tool_calls[index]["function"]["name"] = tool_call_delta.function.name
        if tool_call_delta.function and tool_call_delta.function.arguments:
            current_args[index] += tool_call_delta.function.arguments
            current_tool_calls[index]["function"]["arguments"] = current_args[index]


async def _execute_tool_calls(
    current_tool_calls: Dict[int, Dict], 
    messages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Execute all tool calls and update message history"""
    # Build assistant message with tool calls
    tool_calls_list = list(current_tool_calls.values())
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls_list
    })
    
    # Execute all tool calls
    for tool_call in tool_calls_list:
        tool_name = tool_call["function"]["name"]
        tool_args_str = tool_call["function"]["arguments"]
        
        try:
            # Parse tool arguments
            tool_args = json.loads(tool_args_str)
            
            # Execute tool call
            tool_response = await execute_tool(tool_name, tool_args)
            
            # Add tool response to message history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_response
            })
            
        except Exception as e:
            error_message = f"Tool call error: {str(e)}"
            logger.error(error_message)
            # Add error response to message history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": error_message
            })
    
    return messages


async def _handle_stream_chunk(chunk, msg, current_tool_calls, current_args):
    """Process a single chunk of streaming response"""
    choice = chunk.choices[0]
    delta = choice.delta
    has_tool_call = False
    
    # Handle tool calls
    if delta.tool_calls:
        has_tool_call = True
        await _process_tool_call_delta(
            delta.tool_calls, 
            current_tool_calls, 
            current_args
        )
    
    # Handle regular text response
    elif delta.content:
        await msg.stream_token(delta.content)
    
    return has_tool_call, choice.finish_reason


async def _handle_response(model_info, api_params, enhanced_messages, messages):
    """Handle streaming response"""
    # Create independent message object for this round of response
    msg = cl.Message(content="")
    
    current_tool_calls = {}
    current_args = {}
    has_tool_call = False
    
    try:
        # Prepare LiteLLM parameters - directly pass all necessary parameters
        litellm_params = {
            "model": f"{model_info.provider}/{model_info.model}",
            "stream": True,
            "num_retries": 0,
            "timeout": 30,
            "api_key": model_info.api_key,
            "base_url": model_info.base_url or None,
            **api_params,
        }
        
        logger.info(f"Call LLM: {model_info.provider}/{model_info.model}")
        response = await acompletion(**litellm_params)
        
        try:
            async for chunk in response:
                chunk_has_tool_call, finish_reason = await _handle_stream_chunk(
                    chunk, msg, current_tool_calls, current_args
                )
                
                if chunk_has_tool_call:
                    has_tool_call = True
                
                # Check completion status
                if finish_reason == 'tool_calls':
                    try:
                        # First send the current round's message (if there's content)
                        if msg.content and msg.content.strip():
                            await msg.send()
                        
                        # Execute tool calls
                        enhanced_messages = await _execute_tool_calls(
                            current_tool_calls, 
                            enhanced_messages
                        )
                        return enhanced_messages, True  # Continue to next round
                        
                    except Exception as e:
                        error_message = f"Error when processing tool calls: {str(e)}"
                        logger.error(error_message)
                        await msg.stream_token(f"\n{error_message}\n")
                        await msg.send()
                        return messages, False  # End processing
                
                elif finish_reason:
                    # Other completion reasons, end streaming processing
                    break
            
            # Process media markers and send message
            if not has_tool_call:
                await _process_media_markers(msg)
                if msg.content and msg.content.strip():
                    if save_starter_enabled:
                        # Add save action to AI reply message
                        msg.actions = [
                            build_save_action()
                        ]
                    await msg.send()
                
                # Add assistant message to history
                if msg.content and msg.content.strip():
                    enhanced_messages.append({
                        "role": "assistant", 
                        "content": msg.content
                    })
            else:
                # If there are tool calls, send message directly (tool call related messages are handled elsewhere)
                await msg.send()
            
            return enhanced_messages, False  # End processing
            
        except Exception as e:
            error_str = str(e)
            error_message = format_llm_error_message(model_info.name, error_str)
            logger.error(f"Stream processing error: {error_str}")
            await msg.stream_token(f"\n{error_message}\n")
            # Process media markers even if there's an error
            await _process_media_markers(msg)
            await msg.send()
            return messages, False
            
    except Exception as e:
        error_str = str(e)
        error_message = format_llm_error_message(model_info.name, error_str)
        logger.error(f"LiteLLM call failed: {error_str}")
        await msg.stream_token(f"\n{error_message}\n")
        # Process media markers even if there's an error
        await _process_media_markers(msg)
        await msg.send()
        return messages, False


async def process_streaming_response(
    messages: List[Dict[str, Any]], 
    model_info: ModelInfo,
) -> List[Dict[str, Any]]:
    """
    Process streaming response and tool calls
    
    Args:
        messages: Message history
        model_info: Model information to use
        
    Returns:
        Updated message history
    """
    
    # Clean up steps, handle scenarios where users re-edit sent messages
    chat_messages = cl.chat_context.get()
    if len(chat_messages) >= 2:  # Need at least 2 messages to process
        # Get timestamp of second-to-last message
        second_last_msg = chat_messages[-2]
        second_last_time = second_last_msg.created_at
        
        if second_last_time:
            # Get current steps
            current_steps = cl.user_session.get("current_steps", [])
            # Only keep steps with timestamps before the second-to-last message
            filtered_steps = [
                step for step in current_steps 
                if str(step.created_at) <= second_last_time
            ]
            # Update steps
            cl.user_session.set("current_steps", filtered_steps)
    
    tools = get_all_tools()
    
    # Inject media display system instructions
    enhanced_messages = messages.copy()
    
    while True:  # Loop to handle tool calls
        # Prepare API parameters
        api_params = {
            "messages": enhanced_messages,
        }
        
        # If there are tools, add tool parameters
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"
        
        
        # All parameters are passed through LiteLLM function parameters, not using environment variables
        try:
            enhanced_messages, should_continue = await _handle_response(
                model_info, api_params, enhanced_messages, messages
            )
            
            if not should_continue:
                return enhanced_messages
                
        except Exception as e:
            error_str = str(e)
            error_message = format_llm_error_message(model_info.name, error_str)
            logger.error(f"LiteLLM main loop error: {error_str}")
            # Send error message to user
            error_msg = cl.Message(content=error_message)
            await error_msg.send()
            return enhanced_messages  # Return directly, don't continue loop


# MCP connection management convenience functions
async def handle_mcp_connect(connection, session: ClientSession, tools_converter_func):
    """Handle common logic for MCP connections"""
    tools_result = await session.list_tools()
    openai_tools = tools_converter_func(tools_result.tools)
    
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = openai_tools
    cl.user_session.set("mcp_tools", mcp_tools)

async def handle_mcp_disconnect(name: str):
    """Handle common logic for MCP disconnections"""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    if name in mcp_tools:
        del mcp_tools[name]
    cl.user_session.set("mcp_tools", mcp_tools) 

 