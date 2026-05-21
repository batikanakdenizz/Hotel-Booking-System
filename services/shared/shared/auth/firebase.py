"""Firebase Admin SDK initialization + low-level JWT verification.

Init is a singleton — call `init_firebase_app(...)` once on service startup
(FastAPI lifespan). `verify_firebase_token` is then safe to call from any
request handler.
"""
from __future__ import annotations

import json
import os
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials
import structlog

logger = structlog.get_logger(__name__)


def init_firebase_app(
    *,
    project_id: str,
    service_account_path: str | None = None,
    service_account_json: str | None = None,
) -> firebase_admin.App:
    """Initialize (or return) the singleton Firebase app.

    Supports both env-var conventions documented in .env.example:
      - service_account_path: file on disk (local dev convenience)
      - service_account_json: full JSON as a single-line string (prod / Render)
    PATH wins if both are set.

    Idempotent: calling twice returns the already-initialized app instead of
    raising `ValueError: The default Firebase app already exists`.
    """
    if firebase_admin._apps:  # noqa: SLF001 — official idiom for "is initialized?"
        return firebase_admin.get_app()

    if service_account_path:
        cred = credentials.Certificate(service_account_path)
        source = f"path={service_account_path}"
    elif service_account_json:
        cred = credentials.Certificate(json.loads(service_account_json))
        source = "json env var"
    else:
        raise RuntimeError(
            "Either FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON must be set"
        )

    app = firebase_admin.initialize_app(cred, {"projectId": project_id})
    logger.info("firebase_initialized", project_id=project_id, source=source)
    return app


def init_firebase_from_env() -> firebase_admin.App:
    """Convenience: pull config straight from os.environ.

    Useful for scripts (promote_admin.py) that don't go through the FastAPI
    settings object.
    """
    project_id = os.environ["FIREBASE_PROJECT_ID"]
    return init_firebase_app(
        project_id=project_id,
        service_account_path=os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH"),
        service_account_json=os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"),
    )


def verify_firebase_token(id_token: str) -> dict[str, Any]:
    """Decode and verify a Firebase ID token.

    Returns the decoded claims dict (`uid`, `email`, `iss`, `exp`, ...).
    Raises firebase_admin.auth.InvalidIdTokenError (or subclass) on bad/expired tokens.

    Verification is offline JWT signature validation against cached Google
    public keys — no HTTP roundtrip per request.
    """
    return auth.verify_id_token(id_token)
