"""gateway entry point — single public surface for the hotel-booking platform.

Responsibilities (Plan §4.1):
  - Firebase JWT verify (per route policy)
  - Rate limit (slowapi, default 60/min/IP)
  - CORS (frontend origin)
  - Reverse proxy via httpx
  - Request logging
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.middleware.auth import verify_optional, verify_required
from app.proxy import forward
from app.routes import match_rule
from shared.auth.firebase import init_firebase_app
from shared.logging import configure_logging

logger = configure_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_starting", port=8080)
    init_firebase_app(
        project_id=settings.firebase_project_id,
        service_account_path=settings.firebase_service_account_path,
        service_account_json=settings.firebase_service_account_json,
    )
    timeout = httpx.Timeout(
        connect=settings.proxy_connect_timeout_s,
        read=settings.proxy_read_timeout_s,
        write=settings.proxy_read_timeout_s,
        pool=settings.proxy_connect_timeout_s,
    )
    app.state.http_client = httpx.AsyncClient(timeout=timeout)
    logger.info("service_started")
    try:
        yield
    finally:
        logger.info("service_stopping")
        await app.state.http_client.aclose()
        logger.info("service_stopped")


# ---- App + middlewares -------------------------------------------------------

app = FastAPI(title="Hotel Booking — Gateway", version="0.1.0", lifespan=lifespan)

# CORS: comma-separated origins from env.
_origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)

# Rate limit (per-IP).
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _on_rate_limit(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"rate limit exceeded ({exc.detail})", "code": "rate_limited"},
    )


# ---- Routes ------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@app.api_route("/api/v1/{full_path:path}", methods=PROXY_METHODS)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def proxy_handler(request: Request, full_path: str) -> Response:
    """Single catch-all that fans out to the right downstream service.

    The route-rule decides:
      - which target_base_url to proxy to
      - whether this method requires a valid Firebase token
    """
    path = "/api/v1/" + full_path
    rule = match_rule(path)
    if rule is None:
        raise HTTPException(status_code=404, detail="unknown route")

    if rule.requires_auth(request.method):
        x_user_id: str | None = verify_required(request)
    else:
        x_user_id = verify_optional(request)

    logger.info(
        "proxy_forward",
        method=request.method,
        path=path,
        target=rule.target_base_url,
        x_user_id=x_user_id,
    )

    return await forward(
        request.app.state.http_client,
        target_base_url=rule.target_base_url,
        request=request,
        forwarded_path=path,
        x_user_id=x_user_id,
    )
