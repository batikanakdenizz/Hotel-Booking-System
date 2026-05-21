"""Gateway-side Firebase JWT verification helper.

Centralised here so every route-rule branch shares the same code path.
On success, returns the Firebase UID — caller injects it as X-User-Id when
forwarding to the downstream service.
"""
from __future__ import annotations

from fastapi import HTTPException, Request, status
from firebase_admin import auth as fb_auth

from shared.auth.firebase import verify_firebase_token


def _extract_bearer(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


def verify_required(request: Request) -> str:
    """Returns the Firebase UID, raises 401 if missing/invalid."""
    token = _extract_bearer(request)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing Authorization bearer token")
    try:
        claims = verify_firebase_token(token)
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired")
    except fb_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token revoked")
    except fb_auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {e}")
    return claims["uid"]


def verify_optional(request: Request) -> str | None:
    """Returns the Firebase UID if a valid token is present, None otherwise.

    Malformed/expired tokens are silently treated as anonymous — downstream
    services can still choose to apply auth-conditional logic (e.g. discount
    pricing) but the request isn't blocked.
    """
    token = _extract_bearer(request)
    if token is None:
        return None
    try:
        claims = verify_firebase_token(token)
    except Exception:  # noqa: BLE001 — anonymous fallback by design
        return None
    return claims["uid"]
