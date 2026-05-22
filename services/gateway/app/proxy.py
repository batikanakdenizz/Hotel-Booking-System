"""HTTPX-based reverse proxy core."""
from __future__ import annotations

import httpx
import structlog
from fastapi import Request, Response

logger = structlog.get_logger(__name__)


# Hop-by-hop headers (RFC 7230 §6.1) — must not be forwarded.
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    # These two are managed by httpx based on the actual body, never pass through.
    "host",
    "content-length",
}


async def forward(
    client: httpx.AsyncClient,
    *,
    target_base_url: str,
    request: Request,
    forwarded_path: str,
    x_user_id: str | None,
) -> Response:
    """Forward the incoming request to target_base_url + forwarded_path.

    forwarded_path includes the prefix the downstream service expects
    (e.g. "/api/v1/admin/hotels" — we pass the whole path through, not a
    sub-path). This means downstream routers register the SAME paths as
    the gateway's prefixes — single source of truth for URL shapes.
    """
    # Compose downstream URL.
    qs = request.url.query
    full_url = target_base_url.rstrip("/") + forwarded_path + (f"?{qs}" if qs else "")

    # Filter request headers.
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    if x_user_id is not None:
        headers["X-User-Id"] = x_user_id
    # Force identity encoding for the upstream hop so Cloudflare-in-front-of-Render
    # does not return a brotli body that httpx (without the optional brotli
    # package installed) would fail to decode -- the gateway then forwards raw
    # compressed bytes to the client.
    headers["accept-encoding"] = "identity"

    body = await request.body()

    try:
        upstream = await client.request(
            method=request.method,
            url=full_url,
            headers=headers,
            content=body,
        )
    except httpx.ConnectError as exc:
        logger.warning("upstream_unreachable", url=full_url, error=str(exc))
        return Response(content=b'{"detail":"upstream unreachable"}', status_code=502, media_type="application/json")
    except httpx.TimeoutException as exc:
        logger.warning("upstream_timeout", url=full_url, error=str(exc))
        return Response(content=b'{"detail":"upstream timeout"}', status_code=504, media_type="application/json")

    # Filter response headers — strip hop-by-hop + content-encoding (httpx already decoded).
    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in _HOP_BY_HOP and k.lower() != "content-encoding"
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )
