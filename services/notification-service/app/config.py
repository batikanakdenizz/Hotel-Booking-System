"""notification-service settings."""
from __future__ import annotations

from pydantic import Field

from shared.config import BaseServiceSettings


class NotificationSettings(BaseServiceSettings):
    service_name: str = "notification-service"

    postgres_url: str = Field(description="asyncpg URL (Postgres read-only for occupancy check)")
    rabbitmq_url: str = Field(description="amqps:// URL (CloudAMQP)")

    rabbitmq_exchange: str = "reservations-exchange"
    rabbitmq_queue: str = "q.reservations.notifications"
    rabbitmq_routing_key: str = "reservation.created"

    resend_api_key: str
    email_from: str = "onboarding@resend.dev"

    # X-Cron-Secret header value that Google Cloud Scheduler must send.
    cron_secret: str = Field(description="Shared secret protecting /trigger/nightly")

    # Hotels with availability % below this threshold get a "low capacity" alert.
    # Equivalently: occupancy > 1 - low_availability_threshold.
    low_availability_threshold: float = 0.20
    nightly_window_days: int = 30


settings = NotificationSettings()
