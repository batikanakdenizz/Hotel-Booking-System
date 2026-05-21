"""Nightly low-availability check (Plan §3.4).

For each active hotel, sum (total_rooms × days_in_window) and the actual
available counts across the same window. If the result is below the
`low_availability_threshold` (default 20%), email the hotel's admin_email.

Triggered by Google Cloud Scheduler via POST /trigger/nightly, NOT by the
RabbitMQ consumer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.email import EmailClient
from shared.models import Hotel, Room, RoomAvailability

logger = structlog.get_logger(__name__)


@dataclass
class HotelOccupancyRow:
    hotel_id: str
    name: str
    admin_email: str
    availability_pct: float  # 0.0 - 1.0


async def compute_low_availability(session: AsyncSession) -> list[HotelOccupancyRow]:
    """Return hotels whose next-N-day availability is below the threshold.

    Window: [today, today + nightly_window_days). Inclusive start, exclusive end —
    matches the booking flow's date semantics.
    """
    today = date.today()
    window_end = today + timedelta(days=settings.nightly_window_days)

    # Per-room sub-aggregation FIRST, then group up to hotel level.
    # Computing capacity at the (Hotel JOIN Room JOIN RoomAvailability) JOIN
    # would multiply total_rooms by the number of availability rows — wrong.
    per_room = (
        select(
            Room.hotel_id.label("hotel_id"),
            Room.id.label("room_id"),
            Room.total_rooms.label("total_rooms"),
            func.count(RoomAvailability.id).label("days_in_window"),
            func.coalesce(func.sum(RoomAvailability.available_count), 0).label("avail_in_window"),
        )
        .select_from(Room)
        .outerjoin(
            RoomAvailability,
            (RoomAvailability.room_id == Room.id)
            & (RoomAvailability.date >= today)
            & (RoomAvailability.date < window_end),
        )
        .group_by(Room.hotel_id, Room.id, Room.total_rooms)
        .subquery()
    )

    stmt = (
        select(
            Hotel.id.label("hotel_id"),
            Hotel.name,
            Hotel.admin_email,
            func.sum(per_room.c.total_rooms * per_room.c.days_in_window).label("capacity_seat_days"),
            func.sum(per_room.c.avail_in_window).label("available_seat_days"),
        )
        .select_from(Hotel)
        .join(per_room, per_room.c.hotel_id == Hotel.id)
        .where(Hotel.deleted_at.is_(None))
        .group_by(Hotel.id, Hotel.name, Hotel.admin_email)
    )

    rows = (await session.execute(stmt)).all()
    flagged: list[HotelOccupancyRow] = []
    for r in rows:
        capacity = int(r.capacity_seat_days or 0)
        if capacity == 0:
            continue  # no rooms — skip
        avail_pct = float(r.available_seat_days or 0) / capacity
        if avail_pct < settings.low_availability_threshold:
            flagged.append(
                HotelOccupancyRow(
                    hotel_id=str(r.hotel_id),
                    name=r.name,
                    admin_email=r.admin_email,
                    availability_pct=avail_pct,
                )
            )
    return flagged


def _format_alert_html(row: HotelOccupancyRow) -> tuple[str, str]:
    pct = row.availability_pct * 100
    subject = f"Low availability alert — {row.name}"
    html = f"""
    <h2>Low availability — {row.name}</h2>
    <p>Over the next {settings.nightly_window_days} days, your hotel's
    available capacity is <b>{pct:.1f}%</b> of total
    (threshold {settings.low_availability_threshold * 100:.0f}%).</p>
    <p>Consider adjusting room availability or running a promotion before
    bookings sell out.</p>
    <p style="color:#999;font-size:12px;margin-top:24px">SE 4458 demo project — automated nightly check</p>
    """
    return subject, html


async def run_nightly_check(session: AsyncSession, email: EmailClient) -> dict:
    """Returns a summary dict that /trigger/nightly echoes back to the scheduler."""
    flagged = await compute_low_availability(session)
    sent = 0
    skipped: list[str] = []
    for row in flagged:
        subject, html = _format_alert_html(row)
        ok = await email.send(to=row.admin_email, subject=subject, html=html)
        if ok:
            sent += 1
        else:
            skipped.append(row.hotel_id)
    logger.info("nightly_check_done", flagged=len(flagged), sent=sent, skipped=len(skipped))
    return {
        "flagged_hotels": len(flagged),
        "emails_sent": sent,
        "emails_skipped": skipped,
    }
