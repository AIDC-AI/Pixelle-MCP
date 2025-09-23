# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from typing import Awaitable, Optional, Callable, Any, List, Dict, Tuple
import chainlit as cl
from pydantic import BaseModel
import json
from pathlib import Path
import re
import uuid
import asyncio
import random

from pixelle.utils.os_util import get_data_path, get_src_path

ReplyHandler = Callable[[cl.Message], Awaitable[None]]

class StarterModel(BaseModel):
    label: str
    icon: Optional[str] = None
    image: Optional[str] = None
    reply_handler: Optional[ReplyHandler] = None
    messages: Optional[List[Dict[str, Any]]] = None
    enabled: bool = True
    order: int = 999
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def message(self) -> str:
        """Get the content of the first user message from messages"""
        if not self.messages:
            return ""
        
        # Find the first user message
        for item in self.messages:
            if (item.get("role") == "user" and 
                item.get("type") == "message"):
                return item.get("content", "")
        
        return ""
    
    def to_cl_starter(self) -> cl.Starter:
        """Convert to Chainlit Starter object"""
        return cl.Starter(
            label=self.label,
            message=self.message,
            icon=self.icon,
        )

# Typing effect disabled - direct output mode

# File operation related functions
SYSTEM_STARTERS_DIR = Path(get_src_path("starters"))
CUSTOM_STARTERS_DIR = Path(get_data_path("custom_starters"))

def ensure_starters_dirs():
    """Ensure that the system and user starters directories exist"""
    SYSTEM_STARTERS_DIR.mkdir(parents=True, exist_ok=True)
    CUSTOM_STARTERS_DIR.mkdir(parents=True, exist_ok=True)

def get_system_starters_dir() -> Path:
    """Get the system preset starter directory"""
    return SYSTEM_STARTERS_DIR

def get_custom_starters_dir() -> Path:
    """Get the user custom starter directory"""
    return CUSTOM_STARTERS_DIR

def parse_filename(filename: str) -> Tuple[bool, int, str]:
    """
    Parse the file name format: [_]xxx_label.json
    Returns: (enabled, order, label)
    """
    # Remove the .json suffix
    name = filename.replace('.json', '')
    
    # Check if it starts with _ (disabled mark)
    enabled = True
    if name.startswith('_'):
        enabled = False
        name = name[1:]  # Remove the _ in front
    
    # Match the format: xxx_label
    match = re.match(r'^(\d+)_(.+)$', name)
    if match:
        order = int(match.group(1))
        label = match.group(2)
        return enabled, order, label
    else:
        # If it does not match the format, return the default value
        return enabled, 999, name

def get_next_order_number() -> int:
    """Get the next order number in the user directory"""
    ensure_starters_dirs()
    max_order = 0
    
    # Only consider the order number in the user custom directory
    for starter_file in CUSTOM_STARTERS_DIR.glob("*.json"):
        _, order, _ = parse_filename(starter_file.name)
        if order != 999:  # Ignore the default value
            max_order = max(max_order, order)
    
    return max_order + 1

def load_custom_starter(starter_file: Path) -> Optional[StarterModel]:
    """Load a single custom starter from the file"""
    try:
        # Parse the file name
        enabled, order, expected_label = parse_filename(starter_file.name)
        
        with open(starter_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return StarterModel(
            label=expected_label,
            icon=data.get("icon", "/public/tool.svg"),
            image=data.get("image", None),
            messages=data.get("messages", []),
            enabled=enabled,
            order=order,
        )
    except Exception as e:
        print(f"Error loading starter from {starter_file}: {e}")
        return None

def load_system_starters() -> List[StarterModel]:
    """Load the system preset starters"""
    ensure_starters_dirs()
    system_starters = []
    
    for starter_file in SYSTEM_STARTERS_DIR.glob("*.json"):
        starter = load_custom_starter(starter_file)
        if starter and starter.enabled:  # Only load the enabled starters
            system_starters.append(starter)
    
    # Sort by the order field
    system_starters.sort(key=lambda x: x.order)
    
    return system_starters

def load_custom_starters() -> List[StarterModel]:
    """Load the user custom starters"""
    ensure_starters_dirs()
    custom_starters = []
    
    for starter_file in CUSTOM_STARTERS_DIR.glob("*.json"):
        starter = load_custom_starter(starter_file)
        if starter and starter.enabled:  # Only load the enabled starters
            custom_starters.append(starter)
    
    # Sort by the order field
    custom_starters.sort(key=lambda x: x.order)
    
    return custom_starters

def get_all_starters() -> List[StarterModel]:
    """Get all enabled starters, system preset first, user custom later"""
    system_starters = load_system_starters()
    custom_starters = load_custom_starters()
    
    # System preset first, user custom later
    return system_starters + custom_starters

def convert_message_to_dict(message: cl.Message) -> Dict[str, Any]:
    """Convert cl.Message to dictionary format"""
    message_dict = {
        "created_at": message.created_at,
        "role": "user" if message.type == "user_message" else "ai",
        "type": "message",
        "content": message.content,
    }
    
    # Process elements
    if message.elements:
        elements = []
        for element in message.elements:
            if isinstance(element, cl.Image):
                elements.append({
                    "type": "image",
                    "url": element.url,
                    "size": getattr(element, 'size', 'small')
                })
            elif isinstance(element, cl.Video):
                elements.append({
                    "type": "video",
                    "url": element.url,
                    "size": getattr(element, 'size', 'small')
                })
            elif isinstance(element, cl.Audio):
                elements.append({
                    "type": "audio",
                    "url": element.url,
                    "size": getattr(element, 'size', 'small')
                })
        
        if elements:
            message_dict["elements"] = elements
    
    return message_dict

def convert_step_to_dict(step: cl.Step) -> Dict[str, Any]:
    """Convert cl.Step to dictionary format"""
    return {
        "created_at": step.created_at,
        "role": "ai",
        "type": "step",
        "name": step.name,
        "input": step.input if step.input else {},
        "output": step.output if step.output else ""
    }

async def save_conversation_as_starter(label: str, user_message: str) -> bool:
    """Save the current conversation as starter"""
    try:
        ensure_starters_dirs()
        
        # Get the conversation history
        chat_context = cl.chat_context.get()
        # Build the message array
        pure_messages = []
        for item in chat_context:
            if not item.content and not item.elements:
                continue
            if item.type == "system_message":
                continue
            else:
                pure_messages.append(convert_message_to_dict(item))
        
        
        
        # Get steps from user_session
        current_steps = cl.user_session.get("current_steps", [])
        step_messages = []
        for step in current_steps:
            step_messages.append(convert_step_to_dict(step))
            
        all_messages = pure_messages + step_messages
        all_messages.sort(key=lambda x: x.get("created_at", ""))
        
        # Add \u200B prefix to the first user message to identify starter
        if all_messages:
            first_user_msg = None
            for msg in all_messages:
                if msg.get("role") == "user" and msg.get("type") == "message":
                    first_user_msg = msg
                    break
            if first_user_msg and first_user_msg.get("content"):
                # Add zero width space prefix to identify this is a starter message
                starter_prefix = "\u200B"
                msg_content = first_user_msg["content"]
                if not msg_content.startswith(starter_prefix):
                    first_user_msg["content"] = starter_prefix + msg_content
        
        # Create starter data
        starter_data = {
            "icon": "/public/tool.svg",
            "messages": all_messages
        }
        
        # Generate file name
        order = get_next_order_number()
        filename = f"{order:03d}_{label}.json"
        filepath = CUSTOM_STARTERS_DIR / filename
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(starter_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error saving starter: {e}")
        return False

def build_save_action():
    return cl.Action(
        name="save_as_starter", 
        payload={"value": "save_starter"}, 
        icon="save"
    )

async def show_prompt_dialog(title: str, message: str, placeholder: str = ""):
    """Show custom prompt dialog, return (dialog_id, cancel_callback)"""
    dialog_id = str(uuid.uuid4())
    
    # Create custom element
    prompt_element = cl.CustomElement(
        name="PromptDialog",
        props={
            "open": True,
            "title": title,
            "message": message,
            "placeholder": placeholder,
            "dialogId": dialog_id
        }
    )
    
    # Send dialog
    prompt_msg = cl.Message(content="", elements=[prompt_element])
    await prompt_msg.send()
    
    # Store the dialog information in the user session
    cl.user_session.set(f"prompt_dialog_{dialog_id}", {
        "message": prompt_msg,
        "resolved": False,
        "result": None
    })
    
    # Define cancel callback function
    async def cancel_callback():
        """Clean up prompt dialog related resources"""
        try:
            await prompt_msg.remove()
            # cl.chat_context.remove(prompt_msg)
            cl.user_session.set(f"prompt_dialog_{dialog_id}", None)
        except Exception:
            pass  # Ignore when cleanup fails
    
    return dialog_id, cancel_callback

async def show_alert(alert_type: str, title: str, message: str):
    """Show alert dialog"""
    alert_element = cl.CustomElement(
        name="AlertDialog",
        props={
            "open": True,
            "type": alert_type,
            "title": title,
            "message": message
        }
    )
    
    # Send alert
    alert_msg = cl.Message(content="", elements=[alert_element])
    await alert_msg.send()

@cl.action_callback("prompt_confirmed")
async def on_prompt_confirmed(action):
    """Handle user confirmation input"""
    dialog_id = action.payload.get("dialogId")
    value = action.payload.get("value", "").strip()
    
    if dialog_id:
        dialog_info = cl.user_session.get(f"prompt_dialog_{dialog_id}")
        if dialog_info:
            dialog_info["resolved"] = True
            dialog_info["result"] = value
            cl.user_session.set(f"prompt_dialog_{dialog_id}", dialog_info)

@cl.action_callback("save_as_starter")
async def on_save_starter(action):
    """Handle the action of saving as Starter"""
    try:
        # Get the conversation history
        chat_context = cl.chat_context.get()
        if not chat_context or len(chat_context) < 2:
            await show_alert("error", "Cannot save", "Need conversation content to save as Starter")
            return
        
        # Get the content of the first user message as display use
        first_user_message = None
        for msg in chat_context:
            if isinstance(msg, cl.Message) and msg.type == "user_message":
                first_user_message = msg.content
                break
        
        if not first_user_message:
            await show_alert("error", "Cannot save", "Cannot find user message")
            return
        
        # Show custom prompt dialog
        dialog_id, cancel_callback = await show_prompt_dialog(
            title="Save as Starter",
            message="Please input the label name of Starter (for display on the homepage)",
            placeholder="e.g. Image editing tutorial"
        )
        
        # Wait for user input (wait indefinitely, no timeout)
        import asyncio
        while True:
            await asyncio.sleep(0.1)
            dialog_info = cl.user_session.get(f"prompt_dialog_{dialog_id}")
            if dialog_info and dialog_info.get("resolved"):
                label = dialog_info.get("result")
                break
        
        if not label:
            # User canceled, clean up prompt message
            await cancel_callback()
            return
        
        # Verify the label name
        import re
        if not re.match(r'^[\w\u4e00-\u9fff\-_\s]+$', label):
            # Invalid input, clean up prompt message
            await cancel_callback()
            await show_alert("warning", "Invalid input", "Label name can only contain English, Chinese, numbers, underscores, hyphens and spaces")
            return
        
        # Clean up prompt message after saving
        await cancel_callback()
        
        # Save starter (pass in label only, user_message parameter is no longer used)
        success = await save_conversation_as_starter(label, first_user_message)
        
        
        if success:
            await show_alert("success", "Save successfully", f"Successfully saved as Starter: {label}")
            # Remove action button
            await action.remove()
        else:
            await show_alert("error", "Save failed", "Please check file permissions or contact the administrator")
            
    except Exception as e:
        # Also clean up the state when an exception occurs
        if 'cancel_callback' in locals():
            await cancel_callback()
        await show_alert("error", "Operation failed", str(e))

async def handle_messages(messages: List[Dict[str, Any]]) -> None:
    """Handle the preset answer array"""
    if not messages:
        return
    
    for item in messages:
        role = item.get("role", "ai")
        item_type = item.get("type", "message")
        
        if item_type == "step":
            await handle_step_item(item)
        elif item_type == "message":
            await handle_message_item(item, role)

async def handle_step_item(item: Dict[str, Any]) -> None:
    """Handle the step item"""
    step_name = item.get("name", "Processing...")
    step_input = item.get("input", {})
    step_output = item.get("output", "")
    
    async with cl.Step(name=step_name) as step:
        step.input = step_input
        step.output = step_output

async def send_message_directly(content: str, message_type: str = "assistant_message") -> cl.Message:
    """Send message content directly without typing effect
    
    Args:
        content: The content to output
        message_type: The message type
    """
    message = cl.Message(content=content, type=message_type)
    await message.send()
    return message

async def handle_message_item(item: Dict[str, Any], role: str) -> None:
    """Handle the message item"""
    content = item.get("content", "")
    elements_data = item.get("elements", [])
    
    # Build the element list
    elements = []
    for elem_data in elements_data:
        elem_type = elem_data.get("type", "")
        elem_url = elem_data.get("url", "")
        elem_size = elem_data.get("size", "small")
        
        if elem_type == "image" and elem_url:
            elements.append(cl.Image(url=elem_url, size=elem_size))
        elif elem_type == "video" and elem_url:
            elements.append(cl.Video(url=elem_url, size=elem_size))
        elif elem_type == "audio" and elem_url:
            elements.append(cl.Audio(url=elem_url, size=elem_size))
    
    # Send messages directly without typing effect
    if role == "user":
        # User message - direct output
        message = await send_message_directly(content, message_type="user_message")
    else:
        # AI assistant message - direct output
        message = await send_message_directly(content, message_type="assistant_message")
    
    # After the content output is completed, add elements at once
    if elements:
        message.elements = elements
        await message.update()

@cl.set_starters
async def set_starters():
    return [starter.to_cl_starter() for starter in get_all_starters()]

async def hook_by_starters(message: cl.Message):
    """Hook function: handle the starter message content"""
    
    # Check if it is the first user message
    cl_messages = cl.chat_context.get()
    user_messages = [msg for msg in cl_messages if msg.type == "user_message"]
    is_first_message = len(user_messages) == 1
    if not is_first_message:
        return False
    
    # Strictly match the message content
    for starter in get_all_starters():
        # Get the first user message from messages for matching
        if not starter.messages:
            continue
            
        first_user_item = None
        for item in starter.messages:
            if (item.get("role") == "user" and 
                item.get("type") == "message"):
                first_user_item = item
                break
        
        if not first_user_item:
            continue
            
        starter_message = first_user_item.get("content", "")
        if message.content != starter_message:
            continue
            
        # Check and handle the image elements in the starter
        starter_elements = first_user_item.get("elements", [])
        if starter_elements and not message.elements:
            message.elements = []
            for elem_data in starter_elements:
                elem_type = elem_data.get("type", "")
                elem_url = elem_data.get("url", "")
                elem_size = elem_data.get("size", "small")
                
                if elem_type == "image" and elem_url:
                    message.elements.append(cl.Image(url=elem_url, size=elem_size))
                elif elem_type == "video" and elem_url:
                    message.elements.append(cl.Video(url=elem_url, size=elem_size))
                elif elem_type == "audio" and elem_url:
                    message.elements.append(cl.Audio(url=elem_url, size=elem_size))
            await message.update()
        
        # Handle the message, skip the first user message (already sent)
        if starter.messages and len(starter.messages) > 1:
            await handle_messages(starter.messages[1:])
            return True
        # Then use the traditional reply_handler (backward compatible)
        elif starter.reply_handler:
            await starter.reply_handler(starter)
            return True
    
    return False