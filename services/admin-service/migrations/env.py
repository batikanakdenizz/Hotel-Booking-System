"""Alembic environment — wired to shared.models.Base + POSTGRES_MIGRATION_URL.

Runs synchronously (psycopg2) against Supabase's SESSION pooler (port 5432),
NOT the transaction pooler — Alembic uses named prepared statements that the
transaction pooler rejects. See developing_process.md §1.5 "11. ders".
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context
from dotenv import load_dotenv

# --- Bootstrapping --------------------------------------------------------------

# Make shared/ importable regardless of where alembic is invoked from.
REPO_ROOT = Path(__file__).resolve().parents[3]  # admin-service/migrations/env.py -> repo root
sys.path.insert(0, str(REPO_ROOT / "services" / "shared"))

# Load .env from repo root so POSTGRES_MIGRATION_URL is present.
load_dotenv(REPO_ROOT / ".env")

# Now safe to import the shared metadata.
from shared.models import Base  # noqa: E402

# Alembic config object (reads alembic.ini)
config = context.config

# Inject the runtime URL into alembic's view of the config so it doesn't have
# to be in alembic.ini (which is committed to git — secrets must not live there).
migration_url = os.environ.get("POSTGRES_MIGRATION_URL")
if not migration_url:
    raise RuntimeError(
        "POSTGRES_MIGRATION_URL not set. Run alembic from the repo root with .env loaded."
    )
config.set_main_option("sqlalchemy.url", migration_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without connecting (for reviewing the diff)."""
    context.configure(
        url=migration_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # detect column-type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against the actual database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # one-shot connection — Alembic is not long-lived
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
