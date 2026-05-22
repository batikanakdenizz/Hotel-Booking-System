"""get_hotel_comments tool — calls GET /api/v1/comments/hotels/{id} + /distribution."""
from __future__ import annotations

import httpx

from app.config import settings


async def get_hotel_comments(client: httpx.AsyncClient, *, hotel_id: str) -> dict:
    """Returns a small payload: the top 5 recent comments + the 5-dim distribution."""
    base = settings.gateway_url
    # Accept-Encoding: identity -- see tools/search.py for the rationale.
    headers = {"Accept-Encoding": "identity"}

    try:
        list_resp = await client.get(
            f"{base}/api/v1/comments/hotels/{hotel_id}",
            params={"limit": 5},
            headers=headers,
            timeout=settings.tool_http_timeout_s,
        )
        list_resp.raise_for_status()
        dist_resp = await client.get(
            f"{base}/api/v1/comments/hotels/{hotel_id}/distribution",
            headers=headers,
            timeout=settings.tool_http_timeout_s,
        )
        dist_resp.raise_for_status()
    except httpx.HTTPError as exc:
        return {"error": "transport_error", "detail": str(exc)}

    listing = list_resp.json()
    distribution = dist_resp.json()

    return {
        "total_comments": distribution["total_comments"],
        "averages": {
            "cleanliness": distribution.get("avg_cleanliness"),
            "staff": distribution.get("avg_staff"),
            "amenities": distribution.get("avg_amenities"),
            "comfort": distribution.get("avg_comfort"),
            "eco_friendliness": distribution.get("avg_eco_friendliness"),
            "overall": distribution.get("avg_overall"),
        },
        "recent": [
            {
                "user": c.get("user_display_name") or "anonymous",
                "text": c["text"],
                "overall_rating": c["overall_rating"],
                "created_at": c["created_at"],
            }
            for c in listing.get("items", [])
        ],
    }
