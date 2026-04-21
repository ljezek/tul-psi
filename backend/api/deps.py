from __future__ import annotations

import hmac
import logging

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.auth import get_user_by_id
from db.session import get_session
from models.user import User
from settings import get_settings

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Resolve the authenticated user from the ``session`` HttpOnly JWT cookie.

    Returns the ``User`` record when a valid JWT is present, or ``None`` when
    the request is unauthenticated (no ``session`` cookie).

    Raises HTTP 401 when a token is present but invalid or expired, when the JWT
    payload is malformed, or when it refers to a user that no longer exists.
    Callers that require authentication should treat a ``None`` return value as
    unauthenticated and respond with an appropriate 401/403 themselves.

    CSRF protection is enforced separately via the ``verify_csrf_token``
    dependency registered at the application level.
    """
    token = request.cookies.get("session")
    if token is None:
        # Unauthenticated request — not an error; callers decide whether auth is required.
        return None

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        logger.warning("Invalid or expired JWT; raising HTTP 401.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from None

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
        )

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
        )

    return user


async def require_current_user(
    current_user: User | None = Depends(get_current_user),
) -> User:
    """Resolve the authenticated user, raising HTTP 401 for unauthenticated requests.

    Wraps ``get_current_user`` for endpoints that always require authentication.
    Callers receive a ``User`` instance (never ``None``) or an HTTP 401 response.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    return current_user


async def verify_csrf_token(request: Request) -> None:
    """Enforce Double Submit Cookie CSRF protection on state-changing requests.

    Safe methods (GET, HEAD, OPTIONS) are skipped.  For all mutating methods the
    ``XSRF-TOKEN`` cookie must be present and its value must equal the
    ``X-XSRF-Token`` request header.

    CSRF protection is only enforced for authenticated sessions (where the
    ``session`` cookie is present).  Requests without the session cookie (e.g.,
    initial login, public endpoints) are allowed through — downstream auth
    dependencies handle authentication if required.
    """
    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return

    # If there is no session cookie, this is an unauthenticated request.
    # We skip CSRF check for these as there is no session to hijack.
    if not request.cookies.get("session"):
        return

    cookie_token = request.cookies.get("XSRF-TOKEN")
    if not cookie_token:
        # If session exists, XSRF-TOKEN should have been set during login.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF cookie missing.",
        )

    header_token = request.headers.get("X-XSRF-Token", "")
    if not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed.",
        )


async def get_optional_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Resolve the authenticated user, returning ``None`` on any auth failure.

    A thin wrapper around ``get_current_user`` that catches HTTP 401 responses
    and returns ``None`` instead of propagating them.  This makes it safe to use
    on publicly accessible endpoints: callers with stale or tampered cookies
    still receive the public response rather than a 401.
    """
    try:
        return await get_current_user(request, session)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            # Auth failures on public endpoints are expected; treat as unauthenticated.
            logger.debug("Optional auth: %s; treating request as unauthenticated.", exc.detail)
            return None
        # Non-401 HTTP exceptions (e.g., 500) are not auth errors and must propagate.
        raise
