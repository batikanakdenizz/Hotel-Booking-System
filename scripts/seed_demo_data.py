"""Seed Supabase with a representative dataset for local dev + demo.

Idempotent: re-running clears the existing demo rows (matched by a fixed set
of hotel names) and reseeds. Won't touch unrelated data — production-safe IF
the demo names don't collide.

What gets created:
  - 10 hotels across 7 destinations
  - 3 room types per hotel (Single, Double, Suite)
  - 90 days of availability starting from today, for every room
  - 1 demo user (admin@hotelapp.com — gets role='hotel_admin')
  - 1 demo user (user@hotelapp.com)
  - A handful of sample bookings on user@hotelapp.com so MyBookings has rows

Usage from repo root:
    .venv\\Scripts\\python scripts/seed_demo_data.py
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "services" / "shared"))
load_dotenv(REPO_ROOT / ".env")

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from shared.clients.postgres import create_async_engine_for_service, create_session_factory  # noqa: E402
from shared.models import Booking, Hotel, Room, RoomAvailability, User  # noqa: E402


# --- Demo dataset --------------------------------------------------------------

DEMO_HOTELS: list[dict] = [
    {
        "name": "Hotel Roma Plaza",
        "description": "Luxury 4-star hotel in the heart of Rome's historic centre.",
        "destination": "Rome",
        "address": "Via del Corso 123, 00186 Rome, Italy",
        "latitude": 41.9028, "longitude": 12.4964,
        "star_rating": 4,
        "amenities": ["wifi", "pool", "breakfast", "gym", "parking"],
    },
    {
        "name": "Trastevere Boutique",
        "description": "Cozy boutique stay in Rome's most romantic neighborhood.",
        "destination": "Rome",
        "address": "Vicolo del Cinque 45, 00153 Rome, Italy",
        "latitude": 41.8902, "longitude": 12.4665,
        "star_rating": 3,
        "amenities": ["wifi", "breakfast", "pet_friendly"],
    },
    {
        "name": "Le Marais Suites",
        "description": "Stylish suites a five-minute walk from Place des Vosges.",
        "destination": "Paris",
        "address": "12 Rue des Francs-Bourgeois, 75004 Paris, France",
        "latitude": 48.8566, "longitude": 2.3522,
        "star_rating": 4,
        "amenities": ["wifi", "breakfast", "concierge"],
    },
    {
        "name": "Montmartre View",
        "description": "Boutique hotel with rooftop views of Sacré-Cœur.",
        "destination": "Paris",
        "address": "21 Rue des Abbesses, 75018 Paris, France",
        "latitude": 48.8841, "longitude": 2.3380,
        "star_rating": 3,
        "amenities": ["wifi", "breakfast", "bar"],
    },
    {
        "name": "Sultanahmet Palace",
        "description": "Steps from Hagia Sophia and the Blue Mosque.",
        "destination": "Istanbul",
        "address": "Kabasakal Cad. 1, 34122 Fatih/Istanbul, Türkiye",
        "latitude": 41.0086, "longitude": 28.9802,
        "star_rating": 5,
        "amenities": ["wifi", "pool", "breakfast", "spa", "hammam"],
    },
    {
        "name": "Bosphorus Bay Hotel",
        "description": "Waterfront views over the Bosphorus from every room.",
        "destination": "Istanbul",
        "address": "Çırağan Cad. 32, 34349 Beşiktaş/Istanbul, Türkiye",
        "latitude": 41.0454, "longitude": 29.0146,
        "star_rating": 5,
        "amenities": ["wifi", "pool", "breakfast", "spa", "restaurant"],
    },
    {
        "name": "Manhattan Skyline",
        "description": "Midtown high-rise with sweeping city views.",
        "destination": "New York",
        "address": "350 5th Ave, New York, NY 10118, USA",
        "latitude": 40.7484, "longitude": -73.9857,
        "star_rating": 4,
        "amenities": ["wifi", "gym", "bar", "breakfast"],
    },
    {
        "name": "Gothic Quarter Inn",
        "description": "Charming inn in Barcelona's medieval old town.",
        "destination": "Barcelona",
        "address": "Carrer de la Boqueria 22, 08002 Barcelona, Spain",
        "latitude": 41.3825, "longitude": 2.1769,
        "star_rating": 3,
        "amenities": ["wifi", "breakfast", "pet_friendly"],
    },
    {
        "name": "Sakura Garden",
        "description": "Modern Japanese hospitality in central Tokyo.",
        "destination": "Tokyo",
        "address": "1-1-1 Marunouchi, Chiyoda City, Tokyo 100-0005, Japan",
        "latitude": 35.6812, "longitude": 139.7671,
        "star_rating": 4,
        "amenities": ["wifi", "breakfast", "onsen"],
    },
    {
        "name": "Aegean Breeze Resort",
        "description": "Beachfront resort on Bodrum's western coast.",
        "destination": "Bodrum",
        "address": "Yalıkavak Mah. Sahil Yolu, 48990 Bodrum/Muğla, Türkiye",
        "latitude": 37.1071, "longitude": 27.2870,
        "star_rating": 5,
        "amenities": ["wifi", "pool", "breakfast", "beach", "spa", "restaurant"],
    },
]

ROOM_TYPES: list[dict] = [
    {"room_type": "Single", "capacity": 1, "total_rooms": 8},
    {"room_type": "Double", "capacity": 2, "total_rooms": 12},
    {"room_type": "Suite", "capacity": 4, "total_rooms": 4},
]

ADMIN_EMAIL = "admin@hotelapp.com"
USER_EMAIL = "user@hotelapp.com"


# --- Pricing model — destination tier + room type modifier --------------------

DESTINATION_TIER: dict[str, Decimal] = {
    "Rome": Decimal("180"),
    "Paris": Decimal("220"),
    "Istanbul": Decimal("140"),
    "New York": Decimal("280"),
    "Barcelona": Decimal("160"),
    "Tokyo": Decimal("210"),
    "Bodrum": Decimal("170"),
}
ROOM_MODIFIER: dict[str, Decimal] = {
    "Single": Decimal("0.70"),
    "Double": Decimal("1.00"),
    "Suite": Decimal("2.10"),
}


def price_for(destination: str, room_type: str) -> Decimal:
    base = DESTINATION_TIER.get(destination, Decimal("150"))
    modifier = ROOM_MODIFIER[room_type]
    return (base * modifier).quantize(Decimal("0.01"))


# --- Seeding logic ------------------------------------------------------------

async def wipe_demo_rows(session: AsyncSession) -> None:
    """Idempotency: drop the exact demo hotels (cascade removes rooms + availability)
    and the two demo users (cascade removes their bookings)."""
    demo_names = [h["name"] for h in DEMO_HOTELS]
    # delete bookings before hotels/users (FK pointing to both)
    demo_user_ids = (
        await session.execute(select(User.id).where(User.email.in_([ADMIN_EMAIL, USER_EMAIL])))
    ).scalars().all()
    if demo_user_ids:
        await session.execute(delete(Booking).where(Booking.user_id.in_(demo_user_ids)))
    await session.execute(delete(Hotel).where(Hotel.name.in_(demo_names)))
    await session.execute(delete(User).where(User.email.in_([ADMIN_EMAIL, USER_EMAIL])))
    await session.commit()


async def seed(session: AsyncSession) -> None:
    today = date.today()
    print(f"[seed] starting at {today} -- seeding 90 days of availability")

    # --- Users (admin + regular) --------------------------------------------
    admin = User(
        firebase_uid="seed-admin-placeholder",
        email=ADMIN_EMAIL,
        display_name="Demo Admin",
        role="hotel_admin",
    )
    regular = User(
        firebase_uid="seed-user-placeholder",
        email=USER_EMAIL,
        display_name="Demo User",
        role="user",
    )
    session.add_all([admin, regular])
    await session.flush()
    print(f"[seed] users: admin id={admin.id}, user id={regular.id}")

    # --- Hotels + Rooms + Availability ---------------------------------------
    created_rooms: list[Room] = []
    for spec in DEMO_HOTELS:
        hotel = Hotel(
            name=spec["name"],
            description=spec["description"],
            destination=spec["destination"],
            address=spec["address"],
            latitude=spec["latitude"],
            longitude=spec["longitude"],
            admin_email=ADMIN_EMAIL,
            star_rating=spec["star_rating"],
            amenities=spec["amenities"],
        )
        session.add(hotel)
        await session.flush()  # populate hotel.id

        for rt in ROOM_TYPES:
            room = Room(
                hotel_id=hotel.id,
                room_type=rt["room_type"],
                capacity=rt["capacity"],
                base_price_per_night=price_for(spec["destination"], rt["room_type"]),
                total_rooms=rt["total_rooms"],
            )
            session.add(room)
            await session.flush()
            created_rooms.append(room)

            for offset in range(90):
                session.add(
                    RoomAvailability(
                        room_id=room.id,
                        date=today + timedelta(days=offset),
                        available_count=rt["total_rooms"],
                    )
                )
    await session.flush()
    print(f"[seed] hotels: {len(DEMO_HOTELS)}, rooms: {len(created_rooms)}, "
          f"availability rows: {len(created_rooms) * 90}")

    # --- Sample bookings on the regular user ---------------------------------
    rng = random.Random(42)  # deterministic seed → same demo dataset each time
    sample_size = 5
    for _ in range(sample_size):
        room = rng.choice(created_rooms)
        nights = rng.randint(2, 5)
        start_offset = rng.randint(7, 60)
        check_in = today + timedelta(days=start_offset)
        check_out = check_in + timedelta(days=nights)
        total = (room.base_price_per_night * nights).quantize(Decimal("0.01"))
        booking = Booking(
            user_id=regular.id,
            room_id=room.id,
            hotel_id=room.hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=rng.randint(1, room.capacity),
            total_price=total,
            status="confirmed",
        )
        session.add(booking)
        # Don't decrement availability here — keeps the demo simple and
        # availability fully consistent with what an empty schedule looks like.
    await session.commit()
    print(f"[seed] sample bookings (on {USER_EMAIL}): {sample_size}")


async def main() -> None:
    engine = create_async_engine_for_service(os.environ["POSTGRES_URL"])
    SessionFactory = create_session_factory(engine)
    try:
        async with SessionFactory() as session:
            print("[seed] wiping previous demo rows (idempotency) ...")
            await wipe_demo_rows(session)
            print("[seed] seeding fresh dataset ...")
            await seed(session)
        print("\n[seed] DONE.")
        print(f"[seed] Admin login: {ADMIN_EMAIL} (role=hotel_admin, firebase_uid=seed-admin-placeholder)")
        print(f"[seed] User login:  {USER_EMAIL}  (role=user, firebase_uid=seed-user-placeholder)")
        print()
        print("Note: the firebase_uid values above are PLACEHOLDERS. After the user signs up via")
        print("the frontend, their real Firebase UID replaces the placeholder via")
        print("get_or_create_user (matching on email). For an admin signup, run:")
        print(f"    python scripts/promote_admin.py {ADMIN_EMAIL}")
        print("which preserves the role across the firebase_uid swap.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
