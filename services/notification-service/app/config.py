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

    # Brevo (formerly Sendinblue) transactional email -- the v3 API key.
    # Free tier: 300 emails/day. Verify the sender_email below in
    # Brevo dashboard before first send (Brevo sends a verification mail).
    brevo_api_key: str
    email_from: str = Field(description="Verified Brevo sender address, e.g. you@gmail.com")
    email_from_name: str = "Stayfinder"

    # X-Cron-Secret header value that Google Cloud Scheduler must send.
    cron_secret: str = Field(description="Shared secret protecting /trigger/nightly")

    # Hotels with availability % below this threshold get a "low capacity" alert.
    # Equivalently: occupancy > 1 - low_availability_threshold.
    low_availability_threshold: float = 0.20
    nightly_window_days: int = 30


settings = NotificationSettings()
