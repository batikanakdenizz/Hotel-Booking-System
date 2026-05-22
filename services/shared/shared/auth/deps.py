"""FastAPI dependencies for identity (Firebase) + authorization (Postgres role).

Pattern:
  - `optional_current_user` — lets endpoints behave differently for anon vs logged-in
    (e.g. search applies the 15% discount only when present).
  - `get_current_user` — raises 401 if not authenticated.
  - `get_or_create_user` — also upserts the Postgres `users` row on first sign-in.
  - `require_admin` — adds the role check on top of get_or_create_user.

The classic pattern is to chain them via `Depends(...)` — each dependency
implies the cheaper ones, so FastAPI evaluates the graph once per request.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, NewType, TypedDict

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as fb_auth

from shared.auth.firebase import verify_firebase_token

# SQLAlchemy + ORM are imported lazily inside the DB-backed helpers so that
# services that only need pure-Firebase identity (e.g. comments-service, which
# only uses Mongo) can install shared without the [postgres] extra.
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shared.models import User


class FirebaseClaims(TypedDict, total=False):
    """Subset of firebase_admin.auth.verify_id_token() output we actually use."""

    uid: str
    email: str
    name: str  # optional, only present if displayName was set
    email_verified: bool


_bearer_scheme = HTTPBearer(auto_error=False)


# ---- Pure-identity dependencies ---------------------------------------------

async def optional_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> FirebaseClaims | None:
    """Returns decoded claims if a valid Authorization header is present, else None.

    Use this on endpoints where auth is optional (e.g. search — anon also allowed).
    """
    if creds is None:
        return None
    try:
        return verify_firebase_token(creds.credentials)  # type: ignore[return-value]
    except fb_auth.InvalidIdTokenError:
        # Treat malformed/expired tokens as "anonymous" rather than 401 — caller can
        # still serve the endpoint without discount/owned-bookings filtering.
        return None


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> FirebaseClaims:
    """Returns decoded claims; 401 if missing or invalid token."""
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing Authorization bearer token")
    try:
        return verify_firebase_token(creds.credentials)  # type: ignore[return-value]
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired")
    except fb_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token revoked")
    except fb_auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {e}")


# ---- Identity + Postgres user row -------------------------------------------

def _get_db_session(request: Request) -> AsyncSession:
    """Stub — each service wires this to its own session factory at app setup.

    Replace at service-mount time:

        app.dependency_overrides[_get_db_session] = my_session_dep

    Or define a local `get_session` and use it instead of `get_or_create_user`.
    """
    raise NotImplementedError(
        "Service must override _get_db_session via app.dependency_overrides "
        "or define a local get_or_create_user with its session dep."
    )


async def _get_or_create_user_impl(
    session: AsyncSession,
    claims: FirebaseClaims,
) -> User:
    """Upsert-on-read: insert a `users` row the first time a Firebase UID shows up.

    Pure function — takes a session and claims, returns the row. Service-level
    wrapper (`get_or_create_user`) plugs in the session dependency.
    """
    from sqlalchemy import select

    from shared.models import User

    uid = claims["uid"]
    email = claims.get("email") or f"{uid}@no-email.firebase"
    display_name = claims.get("name")

    result = await session.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(firebase_uid=uid, email=email, display_name=display_name, role="user")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def require_admin_impl(user: User) -> User:
    """Promote-after-Postgres-lookup admin gate. Service wires via Depends chain."""
    if user.role != "hotel_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user


# ---- Service-side helpers ----------------------------------------------------

# Type aliases services can re-export for nicer endpoint signatures:
#     CurrentUser = Annotated[FirebaseClaims, Depends(get_current_user)]
#     AdminUser = Annotated[User, Depends(require_admin)]
CurrentClaims = NewType("CurrentClaims", FirebaseClaims)


def build_get_or_create_user(session_dep):  # noqa: ANN001 — generic FastAPI dep
    """Bind `_get_or_create_user_impl` to a service's actual session dep.

    Example in admin-service:

        from shared.auth.deps import build_get_or_create_user
        get_or_create_user = build_get_or_create_user(get_session)
    """
    from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401 — needed for runtime Depends

    async def get_or_create_user(
        claims: Annotated[FirebaseClaims, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(session_dep)],
    ) -> User:
        return await _get_or_create_user_impl(session, claims)

    return get_or_create_user


def build_require_admin(get_or_create_user_dep):  # noqa: ANN001
    """Bind the admin check on top of a get_or_create_user dep."""

    async def require_admin(
        user: Annotated[User, Depends(get_or_create_user_dep)],
    ) -> User:
        return await require_admin_impl(user)

    return require_admin


# Convenience re-exports for the unbound case (services that already supplied
# their own session dep — they call these via Depends() directly).
get_or_create_user = _get_or_create_user_impl
require_admin = require_admin_impl
