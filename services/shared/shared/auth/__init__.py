"""Auth helpers split into two submodules.

- ``shared.auth.firebase`` -- pure Firebase JWT verify + admin SDK init.
  No DB dependency; safe to import from services that only need to
  validate tokens (e.g. the gateway).
- ``shared.auth.deps`` -- FastAPI dependencies that read the Postgres
  ``users`` table (role check, get-or-create). Pulls in SQLAlchemy.

We intentionally do NOT re-export from ``deps`` at the package level so
that ``from shared.auth.firebase import X`` does not transitively force
SQLAlchemy into pure-proxy services like the gateway.
"""
