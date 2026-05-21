"""In-memory chat session store — one entry per browser tab / session_id.

Lost on service restart by design. The frontend is responsible for issuing
new session_ids on first load (e.g. uuid4().hex). For a portfolio demo,
this is sufficient; a real product would persist to Redis with TTL.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

_SESSIONS: dict[str, list[dict[str, Any]]] = {}
_LOCK = asyncio.Lock()
_TTL_SECONDS = 60 * 60  # 1h: gc anything older than this
_LAST_ACCESS: dict[str, float] = {}


SYSTEM_PROMPT = (
    "You are a helpful hotel booking assistant for the SE 4458 Hotel Booking System demo. "
    "Use the provided tools to search hotels, check comments, and (when the user is signed "
    "in) book rooms.\n\n"
    "Guidelines:\n"
    " - Be concise. Three short sentences max unless the user asks for detail.\n"
    " - When the user gives a destination + dates + guest count, call `search_hotels` first.\n"
    " - Before calling `book_hotel`, confirm the user's choice in plain language.\n"
    " - If the user isn't signed in but asks to book, tell them they need to sign in first.\n"
    " - Today's date is provided in the first system message — use it when the user says "
    "things like 'next month'.\n"
    " - Always present prices with the currency symbol from the tool output.\n"
)


async def get_or_create(session_id: str, today_iso: str) -> list[dict[str, Any]]:
    async with _LOCK:
        _LAST_ACCESS[session_id] = time.time()
        if session_id not in _SESSIONS:
            _SESSIONS[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Today's date is {today_iso}."},
            ]
        return _SESSIONS[session_id]


async def append(session_id: str, message: dict[str, Any]) -> None:
    async with _LOCK:
        _SESSIONS.setdefault(session_id, []).append(message)
        _LAST_ACCESS[session_id] = time.time()


async def replace(session_id: str, messages: list[dict[str, Any]]) -> None:
    """Atomic replacement of the message list — used after a tool-call loop."""
    async with _LOCK:
        _SESSIONS[session_id] = messages
        _LAST_ACCESS[session_id] = time.time()


async def gc_expired() -> int:
    """Sweep dead sessions; call periodically (or just rely on container restart)."""
    now = time.time()
    dropped = 0
    async with _LOCK:
        stale = [sid for sid, ts in _LAST_ACCESS.items() if now - ts > _TTL_SECONDS]
        for sid in stale:
            _SESSIONS.pop(sid, None)
            _LAST_ACCESS.pop(sid, None)
            dropped += 1
    return dropped
