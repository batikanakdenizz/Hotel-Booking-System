"""Firebase JWT verification + FastAPI dependency helpers.

Identity comes from Firebase; authorization (admin role) comes from Postgres
via `users.role`. See Plan §3.2.
"""
from shared.auth.firebase import (
    init_firebase_app,
    init_firebase_from_env,
    verify_firebase_token,
)
from shared.auth.deps import (
    FirebaseClaims,
    build_get_or_create_user,
    build_require_admin,
    get_current_user,
    optional_current_user,
)

__all__ = [
    "init_firebase_app",
    "init_firebase_from_env",
    "verify_firebase_token",
    "FirebaseClaims",
    "get_current_user",
    "optional_current_user",
    "build_get_or_create_user",
    "build_require_admin",
]
