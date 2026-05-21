"""RabbitMQ consumer task — runs for the FastAPI app's whole lifetime.

Subscribes to the `reservation.created` topic via the durable queue
``q.reservations.notifications``. Per Plan §3.3 we use:
  - durable exchange + durable queue + persistent messages (handled by
    publisher in booking-service)
  - manual ack: basic_ack on success, basic_nack(requeue=True) on
    transient error (network blip while sending email, etc.)
  - email-failure isolation: a 4xx from Resend ACKs the message anyway
    (re-queueing wouldn't help, the recipient is the same).
"""
from __future__ import annotations

import asyncio
import json

import aio_pika
import structlog
from aio_pika.abc import AbstractRobustConnection

from app.config import settings
from app.services.email import EmailClient

logger = structlog.get_logger(__name__)


def _format_confirmation_html(payload: dict) -> tuple[str, str]:
    """Return (subject, html_body) for a reservation.created event."""
    subject = f"Booking confirmed — {payload.get('hotel_name', 'your hotel')}"
    name = payload.get("user_display_name") or "guest"
    html = f"""
    <h2 style="margin-bottom:8px">Booking confirmed</h2>
    <p>Hi {name},</p>
    <p>Your booking at <b>{payload.get('hotel_name', '')}</b> is confirmed.</p>
    <table style="border-collapse:collapse">
      <tr><td style="padding:4px 8px;color:#666">Check-in</td><td style="padding:4px 8px"><b>{payload.get('check_in')}</b></td></tr>
      <tr><td style="padding:4px 8px;color:#666">Check-out</td><td style="padding:4px 8px"><b>{payload.get('check_out')}</b></td></tr>
      <tr><td style="padding:4px 8px;color:#666">Guests</td><td style="padding:4px 8px">{payload.get('guests')}</td></tr>
      <tr><td style="padding:4px 8px;color:#666">Total</td><td style="padding:4px 8px"><b>${payload.get('total_price')}</b></td></tr>
      <tr><td style="padding:4px 8px;color:#666">Booking ID</td><td style="padding:4px 8px"><code>{payload.get('booking_id')}</code></td></tr>
    </table>
    <p style="color:#999;font-size:12px;margin-top:24px">SE 4458 demo project — automated message</p>
    """
    return subject, html


async def consume_reservations(connection: AbstractRobustConnection, email: EmailClient, stop_event: asyncio.Event) -> None:
    """Long-running consumer. Cancelled by lifespan on shutdown."""
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.rabbitmq_exchange, type=aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(settings.rabbitmq_queue, durable=True)
    await queue.bind(exchange, routing_key=settings.rabbitmq_routing_key)

    logger.info(
        "consumer_started",
        exchange=settings.rabbitmq_exchange,
        queue=settings.rabbitmq_queue,
        routing_key=settings.rabbitmq_routing_key,
    )

    async with queue.iterator() as q_iter:
        try:
            async for message in q_iter:
                if stop_event.is_set():
                    break
                try:
                    payload = json.loads(message.body)
                except json.JSONDecodeError as exc:
                    logger.error("consumer_bad_json", error=str(exc), raw=message.body[:200])
                    await message.ack()  # poison message — don't requeue
                    continue

                to_email = payload.get("user_email")
                if not to_email:
                    logger.warning("consumer_no_recipient", payload_keys=list(payload.keys()))
                    await message.ack()
                    continue

                subject, html = _format_confirmation_html(payload)
                try:
                    sent = await email.send(to=to_email, subject=subject, html=html)
                    # ACK regardless of `sent` — re-queueing won't change Resend's decision.
                    await message.ack()
                    logger.info(
                        "booking_email_processed",
                        booking_id=payload.get("booking_id"),
                        to=to_email,
                        sent=sent,
                    )
                except Exception as exc:  # noqa: BLE001 — network blip → requeue
                    logger.error(
                        "consumer_transient_error",
                        error=type(exc).__name__,
                        msg=str(exc),
                        booking_id=payload.get("booking_id"),
                    )
                    await message.nack(requeue=True)
        except asyncio.CancelledError:
            logger.info("consumer_cancelled")
            raise
        finally:
            logger.info("consumer_stopped")
