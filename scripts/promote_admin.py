"""Standalone helper to promote a Postgres `users` row to role='hotel_admin'.

Used by:
  - Demo prep: bump `admin@hotelapp.com` to admin before recording the video
  - Operational: emergency admin grant outside the API surface
  - seed_demo_data.py: programmatically promote the seeded admin user

Usage:
    py -3.13 -m venv .venv          # if not already
    .venv\\Scripts\\pip install -r scripts/requirements.txt -e services/shared[postgres]
    .venv\\Scripts\\python scripts/promote_admin.py admin@hotelapp.com

The target user must have signed up via Firebase at least once (so a `users`
row exists). If they haven't, the script exits with a clear message instead
of silently inserting a stub row.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Make shared/ importable when invoked from the repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "services" / "shared"))
load_dotenv(REPO_ROOT / ".env")

from sqlalchemy import select, update  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from shared.clients.postgres import create_async_engine_for_service, create_session_factory  # noqa: E402
from shared.models import User  # noqa: E402


async def promote(email: str) -> int:
    """Return process exit code: 0 = promoted (or already admin), 2 = not found."""
    engine = create_async_engine_for_service(os.environ["POSTGRES_URL"])
    SessionFactory = create_session_factory(engine)

    try:
        async with SessionFactory() as session:  # type: AsyncSession
            user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()

            if user is None:
                print(f"[promote_admin] No user with email {email!r} exists yet.")
                print("                Have them sign up via the frontend (Firebase) first,")
                print("                then run this script again.")
                return 2

            if user.role == "hotel_admin":
                print(f"[promote_admin] {email} is already hotel_admin (uid={user.firebase_uid}). No-op.")
                return 0

            await session.execute(update(User).where(User.id == user.id).values(role="hotel_admin"))
            await session.commit()
            print(f"[promote_admin] Promoted {email} → role=hotel_admin (uid={user.firebase_uid}).")
            return 0
    finally:
        await engine.dispose()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_admin.py <email>")
        return 1
    email = sys.argv[1].strip().lower()
    return asyncio.run(promote(email))


if __name__ == "__main__":
    sys.exit(main())
