"""Async client wrappers for the four external datastores.

Each module exposes simple factory functions; FastAPI services own the
connection lifecycle (open on startup, close on shutdown).
"""
from shared.clients.postgres import (
    create_async_engine_for_service,
    create_session_factory,
    session_dep,
)

__all__ = [
    "create_async_engine_for_service",
    "create_session_factory",
    "session_dep",
]

