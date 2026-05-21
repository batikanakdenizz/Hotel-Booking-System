"""Groq chat orchestration + tool-call loop.

Implements the canonical OpenAI function-calling pattern:
  1. Send messages + tool schemas
  2. If response has tool_calls: execute each, append result, loop
  3. If response has plain content: return it to the user

Iteration cap prevents runaway loops if the LLM gets confused.
"""
from __future__ import annotations

import json

import httpx
import structlog

from app.config import settings
from app.tools import OPENAI_TOOL_SCHEMAS, dispatch_tool

logger = structlog.get_logger(__name__)


async def chat_once(
    client: httpx.AsyncClient,
    *,
    messages: list[dict],
    user_token: str | None,
) -> tuple[str, list[dict]]:
    """Run one user-turn-to-assistant-reply cycle.

    Returns (final_assistant_text, updated_messages_list).
    """
    working = list(messages)  # don't mutate the caller's list until success

    for iteration in range(settings.max_tool_iterations):
        payload = {
            "model": settings.groq_model,
            "messages": working,
            "tools": OPENAI_TOOL_SCHEMAS,
            "tool_choice": "auto",
            "temperature": 0.5,
        }
        try:
            r = await client.post(
                f"{settings.groq_api_base}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                timeout=60.0,
            )
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:300]
            logger.error("groq_http_error", status=exc.response.status_code, body=body)
            raise
        except httpx.HTTPError as exc:
            logger.error("groq_transport_error", error=str(exc))
            raise

        data = r.json()
        choice = data["choices"][0]
        message = choice["message"]

        # Persist the assistant's turn — even tool-call-only turns count.
        working.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return (message.get("content") or "").strip(), working

        # Execute each requested tool, append each result back as a `tool` message.
        for tc in tool_calls:
            fn = tc["function"]
            tool_name = fn["name"]
            tool_args = fn.get("arguments", "{}")
            result_str = await dispatch_tool(
                client,
                name=tool_name,
                arguments=tool_args,
                user_token=user_token,
            )
            working.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": tool_name,
                    "content": result_str,
                }
            )

    # Iteration cap hit — give the LLM one last chance to summarize.
    logger.warning("tool_loop_cap_hit", iterations=settings.max_tool_iterations)
    working.append(
        {
            "role": "system",
            "content": (
                "Tool-iteration budget exhausted. Summarize what you've learned so far "
                "and ask the user how to proceed."
            ),
        }
    )
    final = await client.post(
        f"{settings.groq_api_base}/chat/completions",
        json={
            "model": settings.groq_model,
            "messages": working,
            "temperature": 0.3,
            # Force a plain-text close-out here.
        },
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        timeout=30.0,
    )
    final.raise_for_status()
    closing = final.json()["choices"][0]["message"]
    working.append(closing)
    return (closing.get("content") or "").strip(), working
