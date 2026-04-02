from __future__ import annotations

import logging

import jwt
from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from db.session import get_session
from models.user import User
from settings import Settings, get_settings

logger = logging.getLogger(__name__)


async def get_current_user(
    session_token: str | None = Cookie(default=None, alias="session"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """Return the authenticated ``User`` from the session cookie, or ``None`` if unauthenticated.

    Decodes the JWT stored in the ``session`` HttpOnly cookie.  Returns ``None``
    for unauthenticated requests and for tokens that are expired, malformed, or
    reference a user that no longer exists in the database.

    This dependency is designed for endpoints that are publicly accessible but
    may return additional data when a valid session is present.
    """
    if session_token is None:
        return None

    try:
        payload = jwt.decode(
            session_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        logger.debug(
            "JWT decode failed; treating request as unauthenticated.",
            extra={"jwt_error": type(exc).__name__, "detail": str(exc)},
        )
        return None

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()
