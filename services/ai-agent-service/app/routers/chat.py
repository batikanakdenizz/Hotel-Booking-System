"""POST /api/v1/agent/chat — single endpoint, single payload shape."""
from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app import agent, session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=64)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    iterations_used: int | None = None


def _extract_user_token(request: Request) -> str | None:
    """Pull through whatever Authorization the caller (frontend) sent.

    The agent forwards this token to the gateway when calling tools — that's
    how `book_hotel` gets to authenticate as the actual user.
    """
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip() or None
    return None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, request: Request) -> ChatResponse:
    today = date.today().isoformat()
    messages = await session.get_or_create(payload.session_id, today_iso=today)

    # Snapshot + append user turn, then run the loop.
    messages = list(messages) + [{"role": "user", "content": payload.message}]

    token = _extract_user_token(request)
    http_client = request.app.state.http_client

    reply, updated = await agent.chat_once(
        http_client, messages=messages, user_token=token
    )

    await session.replace(payload.session_id, updated)

    logger.info(
        "chat_completed",
        session_id=payload.session_id,
        user_msg_len=len(payload.message),
        reply_len=len(reply),
        history_len=len(updated),
    )

    return ChatResponse(response=reply, session_id=payload.session_id)
