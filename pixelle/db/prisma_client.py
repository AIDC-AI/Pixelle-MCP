# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from __future__ import annotations

from prisma import Prisma


_prisma: Prisma | None = None


def get_client() -> Prisma:
    global _prisma
    if _prisma is None:
        _prisma = Prisma()
    return _prisma


async def connect() -> None:
    client = get_client()
    if not client.is_connected():
        await client.connect()


async def disconnect() -> None:
    client = get_client()
    if client.is_connected():
        await client.disconnect()
