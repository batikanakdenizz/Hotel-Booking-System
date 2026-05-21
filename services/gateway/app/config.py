"""Gateway settings — service URLs + auth + rate limit + CORS."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


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


settings = GatewaySettings()
