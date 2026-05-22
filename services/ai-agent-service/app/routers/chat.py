"""POST /api/v1/agent/chat — single endpoint, single payload shape."""
from __future__ import annotations

from datetime import date

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app import agent, session
from app.config import settings
from app.tools import search as search_tool

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.get("/debug/config")
async def debug_config() -> dict:
    """Read-only echo of effective config -- handy for diagnosing URL/env bugs."""
    return {
        "gateway_url": settings.gateway_url,
        "groq_model": settings.groq_model,
        "groq_api_base": settings.groq_api_base,
        "max_tool_iterations": settings.max_tool_iterations,
        "tool_http_timeout_s": settings.tool_http_timeout_s,
    }


@router.get("/debug/search")
async def debug_search(request: Request, destination: str = "Rome") -> dict:
    """Bypass the LLM and call the search tool directly.

    Returns the raw tool result so a 'tool_exception' surfaces its real
    detail instead of being paraphrased by the LLM. Hit:

        GET /api/v1/agent/debug/search?destination=Istanbul
    """
    client = request.app.state.http_client
    try:
        result = await search_tool.search_hotels(
            client,
            destination=destination,
            check_in="2026-07-15",
            check_out="2026-07-18",
            guests=2,
        )
    except Exception as exc:  # noqa: BLE001
        return {"error": type(exc).__name__, "detail": str(exc), "gateway_url": settings.gateway_url}
    return {"ok": True, "gateway_url": settings.gateway_url, "result": result}


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
