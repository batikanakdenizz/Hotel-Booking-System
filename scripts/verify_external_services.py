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
    """Connect to the transaction pooler and run SELECT 1.

    statement_cache_size=0 is REQUIRED because Supabase's transaction pooler
    (Supavisor on port 6543) multiplexes client connections onto a smaller
    pool of backend Postgres sessions. Prepared statements are session-level
    in Postgres, so when the pooler reuses a backend that already saw an
    asyncpg-named prepared statement from a previous client, the new client
    gets `DuplicatePreparedStatementError`. Disabling the cache forces every
    statement to be sent fresh (small perf hit, but transaction-pooler safe).

    This same gotcha applies to our SQLAlchemy async engine in Phase 2 —
    pass `connect_args={"prepared_statement_cache_size": 0}` there.
    """
    import asyncpg

    url = os.environ.get("POSTGRES_URL")
    if not url:
        return "skip (POSTGRES_URL not set)"

    # asyncpg.connect wants raw postgres://, strip the SQLAlchemy +asyncpg prefix
    asyncpg_url = url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(asyncpg_url, timeout=10, statement_cache_size=0)
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


def check_firebase() -> str:
    """Initialize firebase_admin with our service account and call a no-op API.

    Validates:
      - JSON credentials parse successfully
      - Project ID matches what's in the credentials
      - The service account has permission to talk to the Identity Platform API
    """
    import json
    import firebase_admin
    from firebase_admin import auth, credentials

    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    sa_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not project_id:
        return "skip (FIREBASE_PROJECT_ID not set)"

    if sa_path:
        sa_path_abs = sa_path if os.path.isabs(sa_path) else os.path.join(REPO_ROOT, sa_path)
        if not os.path.isfile(sa_path_abs):
            raise FileNotFoundError(f"FIREBASE_SERVICE_ACCOUNT_PATH points to a missing file: {sa_path_abs}")
        cred = credentials.Certificate(sa_path_abs)
    elif sa_json:
        cred = credentials.Certificate(json.loads(sa_json))
    else:
        return "skip (neither FIREBASE_SERVICE_ACCOUNT_PATH nor _JSON set)"

    # Initialize only once per process (firebase_admin is a singleton)
    if not firebase_admin._apps:  # noqa: SLF001 — intentional probe of internal state
        firebase_admin.initialize_app(cred, {"projectId": project_id})

    # auth.list_users(max_results=1) → cheap, validates the project access
    page = auth.list_users(max_results=1)
    user_count_hint = "0 users" if not page.users else "≥1 user"
    return f"ok (project={project_id}, {user_count_hint})"


async def check_mongo() -> str:
    """Open an Atlas connection with Motor (async driver) and ping the server."""
    from motor.motor_asyncio import AsyncIOMotorClient

    url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("MONGO_DB_NAME", "hotel_booking_comments")
    if not url:
        return "skip (MONGO_URL not set)"

    # serverSelectionTimeoutMS keeps the failure mode bounded — without it Motor
    # waits 30s before giving up on DNS/auth issues.
    client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=10000)
    try:
        # admin.command("ping") is the canonical MongoDB liveness check.
        await client.admin.command("ping")
        # server_info() gives us the version banner for nicer output.
        info = await client.server_info()
        # Touch the target database so we know auth covers it (free tier user
        # has access to all DBs anyway, but this also proves the URL parses).
        _ = await client[db_name].list_collection_names()
        return f"ok (MongoDB {info['version']}, db={db_name})"
    finally:
        client.close()


async def check_redis() -> str:
    """Connect to Upstash and do a SET / GET / DEL round-trip."""
    from redis.asyncio import Redis

    url = os.environ.get("REDIS_URL")
    if not url:
        return "skip (REDIS_URL not set)"

    client = Redis.from_url(url, socket_timeout=10, socket_connect_timeout=10)
    try:
        # PING — most basic liveness signal.
        pong = await client.ping()
        assert pong is True, f"unexpected PING reply: {pong!r}"

        # Round-trip a real key with TTL to prove writes + TTL work.
        test_key = "verify_external_services:smoke"
        test_value = "ok"
        await client.set(test_key, test_value, ex=60)  # 60s self-cleanup
        got = await client.get(test_key)
        assert got == test_value.encode(), f"GET returned {got!r}"
        await client.delete(test_key)

        # INFO server → banner with version.
        info = await client.info(section="server")
        version = info.get("redis_version", "?")
        return f"ok (Redis {version}, SET/GET/DEL ok)"
    finally:
        await client.aclose()


async def check_rabbitmq() -> str:
    """Open an AMQP connection, publish a persistent message to an ephemeral
    queue, consume it back, and ack. Exercises the full producer+consumer
    pipeline that booking-service and notification-service will use.
    """
    import aio_pika

    url = os.environ.get("RABBITMQ_URL")
    if not url:
        return "skip (RABBITMQ_URL not set)"

    # connect_robust = the production-style client that auto-reconnects on
    # transient drops. We use it here too so the smoke test matches reality.
    connection = await aio_pika.connect_robust(url, timeout=15)
    try:
        channel = await connection.channel()

        # Ephemeral queue — exclusive (only this connection) + auto-delete (vanishes
        # when the connection closes). Keeps the CloudAMQP dashboard clean.
        queue = await channel.declare_queue("", exclusive=True, auto_delete=True)

        # Publish a persistent message via the default exchange. The default
        # exchange routes by queue name, so routing_key == queue.name.
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=b"verify_external_services smoke",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )

        # Pull it back and ack. timeout protects us if delivery silently fails.
        message = await queue.get(timeout=10, fail=False)
        if message is None:
            raise RuntimeError("message published but not received within 10s")
        async with message.process():  # auto-acks on success, nacks on exception
            assert message.body == b"verify_external_services smoke"

        # Best-effort server version (the underlying aiormq connection exposes
        # server_properties; RobustConnection's API path differs across versions
        # so we tolerate AttributeError silently).
        version = "?"
        try:
            underlying = getattr(connection, "_connection", None) or getattr(connection, "connection", None)
            props = getattr(underlying, "server_properties", None) or {}
            v = props.get("version", "?")
            version = v.decode() if isinstance(v, (bytes, bytearray)) else v
        except Exception:  # noqa: BLE001 — purely cosmetic, never blocks the check
            pass
        return f"ok (RabbitMQ {version}, publish+consume+ack ok)"
    finally:
        await connection.close()


# Async wrappers so we can run everything from one event loop ---------------

async def _run_sync(fn: Callable[[], str]) -> str:
    return await asyncio.to_thread(fn)


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

CHECKS: list[tuple[str, Callable[[], Awaitable[str]]]] = [
    ("Postgres (runtime, transaction pooler)", check_postgres_runtime),
    ("Postgres (migration, session pooler)", lambda: _run_sync(check_postgres_migration)),
    ("Firebase Authentication", lambda: _run_sync(check_firebase)),
    ("MongoDB Atlas", check_mongo),
    ("Upstash Redis", check_redis),
    ("CloudAMQP RabbitMQ", check_rabbitmq),
    # Add more checks here as Phase 1 progresses:
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
