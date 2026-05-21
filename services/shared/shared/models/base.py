"""DeclarativeBase + the type annotation map used by every ORM model.

SQLAlchemy 2.0 lets us annotate columns with `Mapped[T]` and have the column
type inferred from the annotation. This file plugs in the project-wide
conventions (UTC timestamps, UUID PKs, JSONB for amenities, etc.) so each
table file stays focused on its own columns.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column


# ---- column conventions ------------------------------------------------------

# Primary key UUID, server defaults to gen_random_uuid()
uuid_pk = Annotated[
    UUID,
    mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()),
]

# Foreign-key UUID — same Postgres type, no default
uuid_fk = Annotated[UUID, mapped_column(PG_UUID(as_uuid=True))]

# Timestamps — always TIMESTAMPTZ with server default UTC NOW()
created_at = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False),
]
updated_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
]
deleted_at = Annotated[
    datetime | None,
    mapped_column(DateTime(timezone=True), nullable=True),
]

# Money column — DECIMAL(10,2) like the plan
money = Annotated[Decimal, mapped_column(Numeric(10, 2), nullable=False)]


class Base(DeclarativeBase):
    """Project-wide declarative base. Every ORM model subclasses this."""

    # Make repr() useful in REPL/logs
    def __repr__(self) -> str:  # pragma: no cover — debug helper
        cols = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__mapper__.columns.keys() if k in ("id", "name", "email"))
        return f"<{self.__class__.__name__} {cols}>"
