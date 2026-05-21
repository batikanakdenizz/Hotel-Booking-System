"""Async Redis client wrapper — used by search-service (cache-aside reads)
and admin-service (cache invalidation on write).
"""
from __future__ import annotations

from redis.asyncio import Redis


def create_redis_client(redis_url: str) -> Redis:
    """Single Redis client per service (internally pooled).

    decode_responses=False is intentional — we cache JSON payloads as bytes,
    decode once in the calling code. This avoids the "what if the value is
    binary" footgun later (e.g. compressed cached pages).

    socket_keepalive=True keeps the connection alive across Upstash's idle
    disconnect timer (~5 min).
    """
    return Redis.from_url(
        redis_url,
        decode_responses=False,
        socket_keepalive=True,
        socket_timeout=10,
        socket_connect_timeout=10,
        # Each client uses one connection per concurrent in-flight command;
        # cap at 20 to stay comfortably under Upstash's per-connection plan limits.
        max_connections=20,
    )
