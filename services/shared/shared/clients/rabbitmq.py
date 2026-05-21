"""RabbitMQ connection + reliable publisher helper.

This module is intentionally split into two layers:
  - `create_rabbitmq_connection`: a robust connection (auto-reconnect)
  - `publish_with_retry`: durable+persistent publish with exponential backoff

Both layers together give us the "B'" mitigation for the dual-write
problem documented in Plan §3.3 (durable queue + persistent message +
3-attempt retry + connect_robust).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import aio_pika
from aio_pika.abc import AbstractRobustConnection
import structlog

logger = structlog.get_logger(__name__)


async def create_rabbitmq_connection(rabbitmq_url: str, timeout: float = 15.0) -> AbstractRobustConnection:
    """Open a RobustConnection — survives transient drops via auto-reconnect.

    Call once on app startup (FastAPI lifespan) and close on shutdown.
    """
    return await aio_pika.connect_robust(rabbitmq_url, timeout=timeout)


async def publish_with_retry(
    connection: AbstractRobustConnection,
    *,
    exchange_name: str,
    routing_key: str,
    payload: dict[str, Any],
    max_attempts: int = 3,
    initial_backoff_s: float = 1.0,
) -> bool:
    """Publish a JSON payload to a durable topic exchange with persistent delivery.

    Returns True on success, False if all attempts failed (caller logs/handles).
    Booking-service should treat False as "DB has the booking, notification
    was lost — log booking_id for manual replay" and still return 201 to the
    user (DB is the source of truth, see Plan §3.3 known limitation).

    Args:
        connection: pre-opened RobustConnection (shared across the service)
        exchange_name: e.g. "reservations-exchange" — declared durable+topic
        routing_key: e.g. "reservation.created"
        payload: JSON-serializable dict
        max_attempts: 3 (1s/2s/4s backoff)
        initial_backoff_s: first backoff value; doubles each retry
    """
    body = json.dumps(payload, default=str).encode()  # default=str → UUID, datetime, Decimal

    for attempt in range(1, max_attempts + 1):
        try:
            # Open a fresh channel per publish — cheap (multiplexed over one TCP).
            async with connection.channel() as channel:
                exchange = await channel.declare_exchange(
                    exchange_name,
                    type=aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )
                await exchange.publish(
                    aio_pika.Message(
                        body=body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        content_type="application/json",
                    ),
                    routing_key=routing_key,
                )
            return True
        except Exception as exc:  # noqa: BLE001 — retry any AMQP / network issue
            if attempt < max_attempts:
                backoff = initial_backoff_s * (2 ** (attempt - 1))
                logger.warning(
                    "rabbitmq_publish_retry",
                    routing_key=routing_key,
                    attempt=attempt,
                    backoff_s=backoff,
                    error=type(exc).__name__,
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    "rabbitmq_publish_failed_terminal",
                    routing_key=routing_key,
                    attempts=max_attempts,
                    error=str(exc),
                    payload_keys=list(payload.keys()),
                )
                return False

    return False  # unreachable but keeps type checker happy
