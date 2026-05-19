"""Base settings using pydantic-settings.

Each service extends `BaseServiceSettings` and adds its own fields.
Values come from environment variables (or a `.env` file if `python-dotenv`
is installed and `env_file` is set).
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Settings shared by every microservice."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="unknown", description="Logical name of the service")
    log_level: str = Field(default="INFO", description="Python logging level")
    environment: str = Field(default="development", description="development | staging | production")
