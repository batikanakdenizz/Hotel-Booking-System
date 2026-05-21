"""admin-service settings (extends the shared base)."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


class AdminSettings(BaseServiceSettings):
    """All env-var inputs admin-service consumes.

    Inherits service_name / log_level / environment from BaseServiceSettings.
    """

    service_name: str = "admin-service"

    postgres_url: str = Field(description="asyncpg URL — transaction pooler (6543)")
    redis_url: str = Field(description="rediss:// URL for cache invalidation")

    firebase_project_id: str
    firebase_service_account_path: str | None = None
    firebase_service_account_json: str | None = None

    hotel_detail_ttl_seconds: int = 86_400
    destination_index_ttl_seconds: int = 21_600


settings = AdminSettings()  # singleton; read .env at import time
