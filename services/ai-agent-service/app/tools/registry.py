"""OpenAI/Groq function-calling schemas + dispatcher.

To add a new tool:
  1. Implement an async function in a sibling module.
  2. Register its function-name + JSON Schema below.
  3. Add a dispatch arm in `dispatch_tool`.
"""
from __future__ import annotations

import json

import httpx
import structlog

from app.tools import booking as booking_tool
from app.tools import comments as comments_tool
from app.tools import search as search_tool

logger = structlog.get_logger(__name__)


OPENAI_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": (
                "Search hotels by destination, check-in/check-out dates, and guest count. "
                "Returns up to 10 hotels with available room types and prices. Prices are "
                "automatically discounted 15% if the user is signed in."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "City or region, e.g. 'Rome'"},
                    "check_in": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                    "check_out": {"type": "string", "description": "ISO date YYYY-MM-DD (exclusive)"},
                    "guests": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["destination", "check_in", "check_out", "guests"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_hotel",
            "description": (
                "Book a specific room of a specific hotel for the requested date range. "
                "Requires the user to be signed in. ALWAYS confirm the user's intent in "
                "natural language before calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "string", "description": "UUID from search_hotels result"},
                    "room_id": {"type": "string", "description": "UUID from search_hotels result"},
                    "check_in": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                    "check_out": {"type": "string", "description": "ISO date YYYY-MM-DD (exclusive)"},
                    "guests": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["hotel_id", "room_id", "check_in", "check_out", "guests"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hotel_comments",
            "description": (
                "Fetch a hotel's recent comments and the 5-dimension rating distribution "
                "(cleanliness, staff, amenities, comfort, eco-friendliness)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "string", "description": "UUID from search_hotels result"},
                },
                "required": ["hotel_id"],
            },
        },
    },
]


async def dispatch_tool(
    client: httpx.AsyncClient,
    *,
    name: str,
    arguments: str,
    user_token: str | None,
) -> str:
    """Route a tool call to its handler, return the JSON-encoded result.

    The string return is what the LLM gets back as the tool message — JSON
    keeps the structure intact for the model's reasoning.
    """
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as exc:
        return json.dumps({"error": "bad_arguments", "detail": str(exc)})

    logger.info("tool_invoked", name=name, args_keys=list(args.keys()))

    try:
        if name == "search_hotels":
            result = await search_tool.search_hotels(client, **args, token=user_token)
        elif name == "book_hotel":
            result = await booking_tool.book_hotel(client, **args, token=user_token)
        elif name == "get_hotel_comments":
            result = await comments_tool.get_hotel_comments(client, **args)
        else:
            result = {"error": "unknown_tool", "name": name}
    except TypeError as exc:
        # Likely a missing/extra argument the LLM hallucinated.
        result = {"error": "bad_arguments_for_tool", "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001 — never crash the chat loop
        logger.error("tool_exception", name=name, error=type(exc).__name__, msg=str(exc))
        result = {"error": "tool_exception", "name": name, "detail": str(exc)}

    return json.dumps(result, default=str)
