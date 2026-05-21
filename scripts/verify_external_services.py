"""Verify that every external service in .env is reachable.

Run from repo root after `pip install -r scripts/requirements.txt`:

    python scripts/verify_external_services.py

Each service is checked independently — one failure does NOT block the rest.
Output uses simple ASCII so it works in any terminal (Windows cmd, PowerShell,
bash). Exits 0 if all checks pass, 1 if any failed.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Awaitable, Callable

from dotenv import load_dotenv

# Load .env from repo root (works regardless of CWD)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(REPO_ROOT, ".env"))


# --------------------------------------------------------------------------
# Individual service checks
# --------------------------------------------------------------------------

async def check_postgres_runtime() -> str:
    """Connect to the transaction pooler and run SELECT 1."""
    import asyncpg

    url = os.environ.get("POSTGRES_URL")
    if not url:
        return "skip (POSTGRES_URL not set)"

    # asyncpg.connect wants raw postgres://, strip the SQLAlchemy +asyncpg prefix
    asyncpg_url = url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(asyncpg_url, timeout=10)
    try:
        version = await conn.fetchval("SELECT version()")
        one = await conn.fetchval("SELECT 1")
        assert one == 1
        # First word of the version banner, e.g. "PostgreSQL"
        return f"ok ({version.split(',')[0]})"
    finally:
        await conn.close()


def check_postgres_migration() -> str:
    """Connect to the session pooler (sync) and run SELECT 1.

    This is the URL Alembic will use for migrations.
    """
    import psycopg2

    url = os.environ.get("POSTGRES_MIGRATION_URL")
    if not url:
        return "skip (POSTGRES_MIGRATION_URL not set)"

    # psycopg2 doesn't understand +psycopg2 suffix in the URL
    pg_url = url.replace("postgresql+psycopg2://", "postgresql://")

    conn = psycopg2.connect(pg_url, connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
        return "ok (session pooler reachable)"
    finally:
        conn.close()


# Async wrappers so we can run everything from one event loop ---------------

async def _run_sync(fn: Callable[[], str]) -> str:
    return await asyncio.to_thread(fn)


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

CHECKS: list[tuple[str, Callable[[], Awaitable[str]]]] = [
    ("Postgres (runtime, transaction pooler)", check_postgres_runtime),
    ("Postgres (migration, session pooler)", lambda: _run_sync(check_postgres_migration)),
    # Add more checks here as Phase 1 progresses:
    # ("Firebase Authentication", check_firebase),
    # ("MongoDB Atlas", check_mongo),
    # ("Upstash Redis", check_redis),
    # ("CloudAMQP RabbitMQ", check_rabbitmq),
    # ("Groq LLM", check_groq),
    # ("Resend Email", check_resend),
]


async def main() -> int:
    print("=" * 70)
    print("External-services smoke test")
    print("=" * 70)

    failures = 0
    for name, fn in CHECKS:
        sys.stdout.write(f"  {name:<55} ... ")
        sys.stdout.flush()
        started = time.perf_counter()
        try:
            result = await fn()
            elapsed_ms = (time.perf_counter() - started) * 1000
            print(f"{result}  [{elapsed_ms:.0f}ms]")
        except Exception as exc:  # noqa: BLE001 — surface every failure
            elapsed_ms = (time.perf_counter() - started) * 1000
            print(f"FAIL  [{elapsed_ms:.0f}ms]")
            print(f"      {type(exc).__name__}: {exc}")
            failures += 1

    print("=" * 70)
    if failures:
        print(f"  {failures} check(s) FAILED.")
    else:
        print("  All checks passed.")
    print("=" * 70)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
