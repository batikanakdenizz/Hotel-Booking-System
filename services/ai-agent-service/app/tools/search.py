"""search_hotels tool — calls GET /api/v1/search via the gateway."""
from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


async def search_hotels(
    client: httpx.AsyncClient,
    *,
    destination: str,
    check_in: str,
    check_out: str,
    guests: int,
    token: str | None = None,
) -> dict:
    """Returns a trimmed-down search result for the LLM to reason over.

    Forwards the user's bearer token if present so the search-service applies
    the 15% discount and the LLM can quote real-pay prices.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{settings.gateway_url}/api/v1/search"
    params = {
        "destination": destination,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "limit": 10,
    }
    try:
        r = await client.get(url, params=params, headers=headers, timeout=settings.tool_http_timeout_s)
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {"error": f"search failed: HTTP {exc.response.status_code}", "detail": exc.response.text[:200]}
    except httpx.HTTPError as exc:
        return {"error": "search failed", "detail": str(exc)}

    data = r.json()
    # Trim payload so the LLM doesn't burn context on noise.
    return {
        "total": data["total"],
        "items": [
            {
                "hotel_id": h["hotel_id"],
                "name": h["name"],
                "destination": h["destination"],
                "star_rating": h.get("star_rating"),
                "amenities": h.get("amenities", []),
                "latitude": h.get("latitude"),
                "longitude": h.get("longitude"),
                "rooms": [
                    {
                        "room_id": rm["room_id"],
                        "room_type": rm["room_type"],
                        "capacity": rm["capacity"],
                        "price_per_night": float(rm["price_per_night"]),
                        "discount_applied": rm["discount_applied"],
                    }
                    for rm in h.get("available_rooms", [])
                ],
            }
            for h in data.get("items", [])
        ],
    }
