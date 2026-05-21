"""search-service settings."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


class SearchSettings(BaseServiceSettings):
    service_name: str = "search-service"

    postgres_url: str = Field(description="asyncpg URL — transaction pooler (6543)")
    redis_url: str = Field(description="rediss:// URL for hotel-detail cache reads")

    firebase_project_id: str
    firebase_service_account_path: str | None = None
    firebase_service_account_json: str | None = None

    hotel_detail_ttl_seconds: int = 86_400      # 24h
    destination_index_ttl_seconds: int = 21_600  # 6h

    discount_rate: float = 0.85  # 15% off for logged-in users


settings = SearchSettings()
