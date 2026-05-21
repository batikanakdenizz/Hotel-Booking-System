"""comments-service settings."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


class CommentsSettings(BaseServiceSettings):
    service_name: str = "comments-service"

    mongo_url: str = Field(description="mongodb+srv:// URL")
    mongo_db_name: str = "hotel_booking_comments"

    firebase_project_id: str
    firebase_service_account_path: str | None = None
    firebase_service_account_json: str | None = None


settings = CommentsSettings()
