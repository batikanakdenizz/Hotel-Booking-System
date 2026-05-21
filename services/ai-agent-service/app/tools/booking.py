"""book_hotel tool — calls POST /api/v1/bookings via the gateway.

Requires the user's bearer token. If absent, return a structured "needs login"
result; the LLM is instructed to ask the user to sign in.
"""
from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


async def book_hotel(
    client: httpx.AsyncClient,
    *,
    hotel_id: str,
    room_id: str,
    check_in: str,
    check_out: str,
    guests: int,
    token: str | None = None,
) -> dict:
    if not token:
        return {
            "error": "not_authenticated",
            "message": "Booking requires a signed-in user — ask them to sign in first.",
        }

    url = f"{settings.gateway_url}/api/v1/bookings"
    body = {
        "hotel_id": hotel_id,
        "room_id": room_id,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = await client.post(url, json=body, headers=headers, timeout=settings.tool_http_timeout_s)
    except httpx.HTTPError as exc:
        return {"error": "transport_error", "detail": str(exc)}

    if r.status_code == 201:
        data = r.json()
        return {
            "ok": True,
            "booking_id": data["id"],
            "total_price": data["total_price"],
            "check_in": data["check_in"],
            "check_out": data["check_out"],
            "notification_dispatched": data.get("notification_dispatched", True),
        }
    try:
        detail = r.json().get("detail")
    except Exception:  # noqa: BLE001
        detail = r.text[:200]
    return {"error": f"booking_failed_{r.status_code}", "detail": detail}
