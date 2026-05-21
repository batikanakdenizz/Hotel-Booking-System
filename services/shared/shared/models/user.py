"""users table — Postgres-side identity mirror of Firebase Auth users.

We do NOT store passwords here (Firebase owns that). This row exists so we
can attach app-level state to a Firebase UID: role, display preferences,
booking foreign keys, etc.
"""
from __future__ import annotations

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base, created_at, uuid_pk


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid_pk]
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 'user' | 'hotel_admin' — gate on /api/v1/admin/* via require_admin dep.
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="user")
    created_at: Mapped[created_at]

    __table_args__ = (
        Index("idx_users_firebase_uid", "firebase_uid"),
    )
