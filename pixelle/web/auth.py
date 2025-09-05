# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import chainlit as cl
from pixelle.settings import settings

chainlit_auth_enabled = settings.chainlit_auth_enabled

if chainlit_auth_enabled:
    @cl.password_auth_callback
    def auth_callback(username: str, password: str):
        if (username, password) == ("dev", "dev"):
            return cl.User(
                identifier="dev", metadata={"role": "user", "provider": "credentials"}
            )
        else:
            return None
