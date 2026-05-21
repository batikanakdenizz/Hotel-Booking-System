"""booking-service settings."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


class BookingSettings(BaseServiceSettings):
    service_name: str = "booking-service"

    postgres_url: str = Field(description="asyncpg URL — transaction pooler (6543)")
    rabbitmq_url: str = Field(description="amqps:// URL — CloudAMQP or local broker")

    firebase_project_id: str
    firebase_service_account_path: str | None = None
    firebase_service_account_json: str | None = None

    # Durable + persistent publish target (Plan §5.4)
    rabbitmq_exchange: str = "reservations-exchange"
    rabbitmq_routing_key: str = "reservation.created"
    rabbitmq_publish_max_retries: int = 3
    rabbitmq_publish_timeout_s: int = 10

    # Logged-in users always get the 15% discount on booking pricing too —
    # the price they saw on the search/detail page is what they pay.
    discount_rate: float = 0.85


settings = BookingSettings()
