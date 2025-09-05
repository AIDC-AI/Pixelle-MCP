# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from pixelle.utils.file_uploader import upload
import chainlit as cl

def messages_from_chaintlit_to_openai(cl_messages: list[cl.Message]) -> list[dict]:
    messages = []
    for cl_message in cl_messages:
        content = cl_message.content
        elements = cl_message.elements
        if elements:
            ext_info = f"\n\nAttachments of current message:"
            for i, element in enumerate(elements):
                url = element.url or upload(element.path)
                ext_info += f"\n{i+1}. Type: {element.mime}, Name: {element.name}, URL: {url}"
            content += ext_info
        
        if cl_message.type == "assistant_message":
            messages.append({"role": "assistant", "content": content})
        elif cl_message.type == "user_message":
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "system", "content": content})

    return messages
