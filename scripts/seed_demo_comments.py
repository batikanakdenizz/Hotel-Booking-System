"""Seed demo comments into MongoDB Atlas so the comments tab + rating chart
look populated for the demo. Idempotent on (hotel_id, user_id, text).

Run from the repo root after the Postgres seed has run (hotel IDs come from
search-service):

    python scripts/seed_demo_comments.py

Reads MONGO_URL + MONGO_DB_NAME from the project's `.env`.
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import gzip
import json as jsonlib

import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

try:
    import brotli  # type: ignore
except ImportError:  # pragma: no cover -- optional dep
    brotli = None  # type: ignore


def _decode_response(r: httpx.Response) -> dict:
    """Decompress + json-parse a response, working around brotli/httpx quirks.

    httpx is supposed to auto-decode br/gzip when the right packages are
    installed, but on some Windows + Python 3.13 setups r.content still
    contains the raw compressed bytes. Try the easy path; on failure, try
    every known codec on the raw bytes until one parses.
    """
    body: bytes = r.content
    candidates = [("identity", lambda b: b)]
    if brotli is not None:
        candidates.append(("brotli", lambda b: brotli.decompress(b)))
    candidates.append(("gzip", lambda b: gzip.decompress(b)))
    for name, fn in candidates:
        try:
            return jsonlib.loads(fn(body).decode("utf-8"))
        except Exception:
            continue
    raise RuntimeError(f"could not decode response body (CE={r.headers.get('content-encoding')!r}, first bytes={body[:8].hex()})")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(REPO_ROOT, ".env"))

GATEWAY_URL = os.environ.get("DEMO_GATEWAY_URL", "https://hbs-gateway.onrender.com")

# 12 plausible comments across the 5-dim rating space. We loop these over
# every hotel returned by the search endpoint so each city has reviews.
COMMENTS_POOL: list[dict[str, Any]] = [
    {
        "text": "Spotless room, generous breakfast spread, and the staff went out of their way to recommend local spots. Already planning a return visit.",
        "ratings": {"cleanliness": 10, "staff": 10, "amenities": 9, "comfort": 9, "eco_friendliness": 7},
        "user_display_name": "Elif K.",
    },
    {
        "text": "Comfortable bed and quiet street, but the wifi dropped a couple of times during my work-from-room day. Still solid value for the location.",
        "ratings": {"cleanliness": 8, "staff": 8, "amenities": 7, "comfort": 9, "eco_friendliness": 6},
        "user_display_name": "Tomasz P.",
    },
    {
        "text": "Five-star service, period. Concierge arranged a late check-out and a same-day laundry without a flicker. Will book again.",
        "ratings": {"cleanliness": 9, "staff": 10, "amenities": 9, "comfort": 10, "eco_friendliness": 7},
        "user_display_name": "Yuki M.",
    },
    {
        "text": "Friendly staff, charming building, but the air conditioning was loud and the bathroom was tight. Decent for a short stay.",
        "ratings": {"cleanliness": 7, "staff": 9, "amenities": 6, "comfort": 6, "eco_friendliness": 6},
        "user_display_name": "Anna L.",
    },
    {
        "text": "Lovely terrace breakfast and a thoughtful turn-down service. The eco-friendly toiletries were a nice touch.",
        "ratings": {"cleanliness": 9, "staff": 9, "amenities": 8, "comfort": 9, "eco_friendliness": 10},
        "user_display_name": "Sofia D.",
    },
    {
        "text": "Loved the rooftop view but the elevator was out for half my stay. Staff handled it well, otherwise everything was good.",
        "ratings": {"cleanliness": 8, "staff": 8, "amenities": 6, "comfort": 7, "eco_friendliness": 6},
        "user_display_name": "Marko V.",
    },
    {
        "text": "Modern, minimal, and very quiet. Kettle, robe, and slippers in the room — small things that make a difference.",
        "ratings": {"cleanliness": 9, "staff": 8, "amenities": 9, "comfort": 9, "eco_friendliness": 7},
        "user_display_name": "Liam J.",
    },
    {
        "text": "Pool was clean and never crowded. Could not fault the cleaning team — they were thorough and discreet.",
        "ratings": {"cleanliness": 10, "staff": 8, "amenities": 9, "comfort": 8, "eco_friendliness": 7},
        "user_display_name": "Hannah B.",
    },
    {
        "text": "Cozy room with nice bedding. Felt like a great value, especially with the member discount. Would recommend to friends.",
        "ratings": {"cleanliness": 8, "staff": 9, "amenities": 7, "comfort": 9, "eco_friendliness": 7},
        "user_display_name": "Batuhan A.",
    },
    {
        "text": "Great location, friendly check-in. Breakfast was a bit limited but tasty. Linens looked freshly washed daily.",
        "ratings": {"cleanliness": 9, "staff": 9, "amenities": 7, "comfort": 8, "eco_friendliness": 6},
        "user_display_name": "Léa P.",
    },
    {
        "text": "Eco-friendly hotel done right — refill bottles, no single-use plastics, and the staff explained their recycling program when asked.",
        "ratings": {"cleanliness": 9, "staff": 10, "amenities": 8, "comfort": 8, "eco_friendliness": 10},
        "user_display_name": "Henrik S.",
    },
    {
        "text": "Comfortable beds and a strong shower. The neighborhood was quieter than expected, perfect for a city break.",
        "ratings": {"cleanliness": 8, "staff": 7, "amenities": 7, "comfort": 9, "eco_friendliness": 6},
        "user_display_name": "Mei C.",
    },
]

# Cities seeded in seed_demo_data.py — query each through the public search
# endpoint to discover their hotel IDs.
SEED_CITIES = ["Rome", "Paris", "Istanbul", "New York", "Barcelona", "Tokyo", "Bodrum"]


def _avg(r: dict[str, int]) -> float:
    return round(sum(r.values()) / 5, 2)


async def discover_hotels() -> list[dict[str, str]]:
    """Return [{hotel_id, name, destination}] for every seeded hotel."""
    print(f"[seed-comments] discovering hotels via {GATEWAY_URL}")
    out: list[dict[str, str]] = []
    # Force identity/gzip only -- avoids brotli decode quirks on some local envs.
    headers = {"Accept-Encoding": "gzip, deflate"}
    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        for city in SEED_CITIES:
            r = await client.get(
                f"{GATEWAY_URL}/api/v1/search",
                params={
                    "destination": city,
                    "check_in": "2026-07-01",
                    "check_out": "2026-07-03",
                    "guests": 2,
                },
            )
            r.raise_for_status()
            body = _decode_response(r)
            for h in body.get("items", []):
                out.append({"hotel_id": h["hotel_id"], "name": h["name"], "destination": h["destination"]})
    print(f"[seed-comments] found {len(out)} hotels")
    for h in out:
        print(f"  - [{h['destination']}] {h['name']}")
    return out


async def seed_comments(hotels: list[dict[str, str]]) -> None:
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ.get("MONGO_DB_NAME", "hotel_booking_comments")
    print(f"[seed-comments] connecting to Mongo db={db_name}")

    client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_url)
    coll = client[db_name]["comments"]

    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc)
    random.seed(42)

    for h in hotels:
        # 4-6 comments per hotel, deterministic so re-running stays idempotent.
        n = 4 + (sum(map(ord, h["hotel_id"])) % 3)
        chosen = random.sample(COMMENTS_POOL, n)
        for i, c in enumerate(chosen):
            doc = {
                "hotel_id": h["hotel_id"],
                "user_id": f"demo-seed-{h['destination'].lower()}-{i}",
                "user_display_name": c["user_display_name"],
                "text": c["text"],
                "ratings": c["ratings"],
                "overall_rating": _avg(c["ratings"]),
                "created_at": now - timedelta(days=random.randint(2, 90)),
                "deleted_at": None,
            }
            # Idempotency: skip if a doc with same (hotel_id, user_id, text) exists.
            existing = await coll.find_one(
                {"hotel_id": doc["hotel_id"], "user_id": doc["user_id"], "text": doc["text"]}
            )
            if existing is not None:
                skipped += 1
                continue
            await coll.insert_one(doc)
            inserted += 1

    print(f"[seed-comments] done: inserted={inserted} skipped={skipped}")
    client.close()


async def main() -> int:
    try:
        hotels = await discover_hotels()
    except Exception as exc:  # noqa: BLE001
        print(f"[seed-comments] FAILED to discover hotels: {exc}", file=sys.stderr)
        return 1
    if not hotels:
        print("[seed-comments] no hotels found; nothing to seed", file=sys.stderr)
        return 1
    try:
        await seed_comments(hotels)
    except Exception as exc:  # noqa: BLE001
        print(f"[seed-comments] FAILED to seed Mongo: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
