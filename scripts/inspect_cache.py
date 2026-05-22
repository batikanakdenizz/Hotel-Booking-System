"""Inspect the production Redis cache to verify hotel-detail caching works.

Walks the cache:
  - lists every hotel:* key, shows TTL + payload preview
  - lists every destination:*:hotel_ids set, shows members
  - hits the public search endpoint once for a city that has no cache key,
    then re-inspects to prove the new entry appeared

Reads REDIS_URL from the local .env.
"""
from __future__ import annotations

import asyncio
import gzip
import json
import os
import sys
from pathlib import Path

import brotli
import httpx
from dotenv import load_dotenv
from redis.asyncio import Redis

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

REDIS_URL = os.environ["REDIS_URL"]
GATEWAY = os.environ.get("DEMO_GATEWAY_URL", "https://hbs-gateway.onrender.com")


def _decode(r: httpx.Response) -> dict:
    body = r.content
    for fn in [lambda b: b, lambda b: brotli.decompress(b), lambda b: gzip.decompress(b)]:
        try:
            return json.loads(fn(body).decode("utf-8"))
        except Exception:
            continue
    raise RuntimeError("could not decode body")


async def dump_keys(redis: Redis, label: str, pattern: str) -> list[str]:
    print(f"\n=== {label} (pattern={pattern}) ===")
    keys: list[str] = []
    async for k in redis.scan_iter(match=pattern):
        ttl = await redis.ttl(k)
        ttl_str = f"{ttl}s ({ttl/3600:.1f}h)" if ttl > 0 else f"{ttl}"
        ktype = await redis.type(k)
        if ktype == "string":
            raw = await redis.get(k)
            preview = (raw or "")[:120].replace("\n", " ")
            print(f"  {k:50}  ttl={ttl_str:18}  preview={preview}...")
        elif ktype == "set":
            members = await redis.smembers(k)
            print(f"  {k:50}  ttl={ttl_str:18}  members={list(members)}")
        else:
            print(f"  {k:50}  ttl={ttl_str:18}  type={ktype}")
        keys.append(k)
    if not keys:
        print("  (no keys)")
    return keys


async def main() -> int:
    redis: Redis = Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        print("=" * 70)
        print("STEP 1 -- Snapshot of cache RIGHT NOW")
        print("=" * 70)
        await dump_keys(redis, "Hotel-detail entries", "hotel:*")
        await dump_keys(redis, "Destination index sets", "destination:*")

        # Trigger a cache miss on a city we may not have hit recently.
        print()
        print("=" * 70)
        print("STEP 2 -- Hitting /api/v1/search?destination=Bodrum to populate cache")
        print("=" * 70)
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(
                f"{GATEWAY}/api/v1/search",
                params={
                    "destination": "Bodrum",
                    "check_in": "2026-07-15",
                    "check_out": "2026-07-18",
                    "guests": 2,
                },
                headers={"Accept-Encoding": "identity"},
            )
            r.raise_for_status()
            body = _decode(r)
        hotel_id = body["items"][0]["hotel_id"] if body["items"] else None
        print(f"  search returned {len(body['items'])} hotel(s); first hotel_id={hotel_id}")

        print()
        print("=" * 70)
        print("STEP 3 -- Snapshot AFTER the search call")
        print("=" * 70)
        await dump_keys(redis, "Hotel-detail entries", "hotel:*")
        await dump_keys(redis, "Destination index sets", "destination:*")

        if hotel_id:
            print()
            print("=" * 70)
            print(f"STEP 4 -- Full payload of hotel:{hotel_id}")
            print("=" * 70)
            raw = await redis.get(f"hotel:{hotel_id}")
            if raw:
                print(json.dumps(json.loads(raw), indent=2)[:1200])
            else:
                print("  (key not in cache)")
        return 0
    finally:
        await redis.aclose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
