from __future__ import annotations

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
    the request is unauthenticated (no cookie or missing/invalid token).
    Raises HTTP 401 only when a token *is* present but is invalid or refers to
    a user that no longer exists — callers that require authentication should
    check for ``None`` and raise their own 401/403 as needed.

    CSRF note: per the Double Submit Cookie spec, state-changing requests should
    also carry an ``X-XSRF-Token`` header.  That validation is intentionally
    deferred (mocked) here while SMTP / frontend integration is still in
    progress.

    # TODO: Replace the CSRF mock below with real Double Submit Cookie validation
    # once the frontend sends the ``X-XSRF-Token`` header on state-changing
    # requests (PATCH, POST, DELETE).
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
