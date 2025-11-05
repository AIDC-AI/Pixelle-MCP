# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from __future__ import annotations

from typing import Any, Optional
import json
import chainlit as cl

from .prisma_client import get_client


async def get_or_create_user(identifier: Optional[str], name: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> str:
    prisma = get_client()
    unique_identifier = identifier or "anonymous"

    existing = await prisma.user.find_unique(where={"identifier": unique_identifier})
    if existing:
        return existing.id

    created = await prisma.user.create(
        data={
            "identifier": unique_identifier,
            "name": name,
            "metadata": json.dumps(metadata or {}),
        }
    )
    return created.id


async def get_or_create_session(user_id: Optional[str], title: Optional[str] = None) -> str:
    prisma = get_client()

    # Prefer Chainlit session id as external id for idempotency
    session_external_id = None
    try:
        session_external_id = getattr(cl.context.session, "id", None)
    except Exception:
        session_external_id = None

    if session_external_id:
        existing = await prisma.chatsession.find_unique(where={"externalId": session_external_id})
        if existing:
            return existing.id

    created = await prisma.chatsession.create(
        data={
            "userId": user_id,
            "title": title or None,
            "externalId": session_external_id,
        }
    )
    return created.id


async def save_message(session_id: str, role: str, content: str, metadata: Optional[dict[str, Any]] = None) -> str:
    prisma = get_client()
    created = await prisma.message.create(
        data={
            "sessionId": session_id,
            "role": role,
            "content": content or "",
            "metadata": json.dumps(metadata or {}),
        }
    )
    return created.id


async def ensure_session_started(default_title: Optional[str] = None) -> str:
    """Ensure a DB chat session exists and cache ids in user_session."""
    user_session = cl.user_session

    db_session_id = user_session.get("db_session_id")
    if db_session_id:
        return db_session_id

    # Try to infer user info from chainlit auth
    identifier = None
    name = None
    metadata = None
    try:
        user = user_session.get("user") or None
        if user:
            identifier = getattr(user, "identifier", None)
            name = getattr(user, "name", None)
            metadata = getattr(user, "metadata", None)
    except Exception:
        pass

    db_user_id = await get_or_create_user(identifier, name=name, metadata=metadata)
    db_session_id = await get_or_create_session(db_user_id, title=default_title)

    user_session.set("db_user_id", db_user_id)
    user_session.set("db_session_id", db_session_id)
    return db_session_id
