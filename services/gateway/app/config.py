"""Gateway settings — service URLs + auth + rate limit + CORS."""
from __future__ import annotations

from pydantic import Field, field_validator

from shared.config import BaseServiceSettings


def _normalize_url(v: str) -> str:
    """Accept either bare hostname or full URL; produce a full URL.

    Render's `fromService.property: host` returns the bare service name in
    practice, which httpx cannot reach. Auto-prefixing with https:// turns
    operator/Blueprint mistakes into a no-op instead of a 502 storm.
    """
    v = (v or "").strip().rstrip("/")
    if not v:
        raise ValueError("URL must not be empty")
    if "://" not in v:
        scheme = "http" if v.startswith(("localhost", "127.")) else "https"
        v = f"{scheme}://{v}"
    return v


class GatewaySettings(BaseServiceSettings):
    service_name: str = "gateway"

    # Downstream service URLs — set from .env / docker-compose / Render env.
    admin_service_url: str = "http://127.0.0.1:8001"
    search_service_url: str = "http://127.0.0.1:8002"
    booking_service_url: str = "http://127.0.0.1:8003"
    comments_service_url: str = "http://127.0.0.1:8004"
    notification_service_url: str = "http://127.0.0.1:8005"
    agent_service_url: str = "http://127.0.0.1:8006"

    # Firebase — gateway verifies tokens once and forwards X-User-Id.
    firebase_project_id: str
    firebase_service_account_path: str | None = None
    firebase_service_account_json: str | None = None

    # CORS — comma-separated origins.
    cors_allowed_origins: str = "http://localhost:5173"

    # Rate limit.
    rate_limit_per_minute: int = 60

    # httpx timeouts (seconds). AI agent path can take longer (LLM call).
    proxy_connect_timeout_s: float = 5.0
    proxy_read_timeout_s: float = 60.0

    @field_validator(
        "admin_service_url",
        "search_service_url",
        "booking_service_url",
        "comments_service_url",
        "notification_service_url",
        "agent_service_url",
    )
    @classmethod
    def _coerce_url(cls, v: str) -> str:
        return _normalize_url(v)


settings = GatewaySettings()
