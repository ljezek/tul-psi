from __future__ import annotations

import logging
import random
import string
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from db import auth as db_auth
from models import OtpToken, User
from services.email import EmailSender, EmailTemplate
from settings import get_settings

logger = logging.getLogger(__name__)

# Maximum number of failed verification attempts before a token is invalidated.
_MAX_OTP_ATTEMPTS = 5

# JWT session duration — 8 hours matching the design specification.
_JWT_TTL_HOURS = 8


def _generate_otp() -> str:
    """Return a cryptographically random 6-digit numeric OTP string."""
    return "".join(random.SystemRandom().choices(string.digits, k=6))


def _hash_otp(otp: str) -> str:
    """Return a bcrypt hash of *otp* encoded as a UTF-8 string.

    A fresh salt is generated for every call so each token hash is unique.
    The salt is embedded in the returned hash string, so no separate column is
    needed; ``bcrypt.checkpw`` extracts it automatically during verification.
    """
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def _create_jwt(user: User) -> str:
    """Return a signed JWT encoding *user*'s identity and role.

    The token expires after ``_JWT_TTL_HOURS`` hours.  It is intended to be
    stored in an HttpOnly cookie so that JavaScript cannot read it.
    """
    settings = get_settings()
    payload = {
        "user_id": user.id,
        "role": user.role.value,
        "exp": datetime.now(UTC) + timedelta(hours=_JWT_TTL_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def request_otp(email: str, session: AsyncSession) -> None:
    """Generate an OTP for *email* and persist its hash in the database.

    The response is deliberately identical whether or not the email is
    registered; this prevents user-enumeration attacks (see DESIGN.md).

    Any previously active (non-used) tokens for the user are invalidated before
    the new token is inserted to prevent token accumulation and limit the attack
    surface if an earlier code was intercepted.
    """
    user = await db_auth.get_user_by_email(session, email)

    if user is None or not user.is_active:
        # Silent success — do not reveal that the address is not registered or is inactive.
        logger.warning(
            "OTP requested for unregistered or inactive address; no token created.",
            extra={"email": email},
        )
        return

    if user.id is None:
        # Guard against a partially-constructed object that was never persisted.
        logger.warning(
            "User record has no primary key; OTP generation skipped.",
            extra={"email": email},
        )
        return

    await db_auth.invalidate_active_otp_tokens(session, user.id)

    otp = get_settings().e2e_otp_override or _generate_otp()
    token = OtpToken(user_id=user.id, token_hash=_hash_otp(otp))
    db_auth.add_otp_token(session, token)
    # Commit here — this is the full unit of work: invalidate old tokens and
    # insert the new one must succeed or fail together.
    await session.commit()

    logger.info("OTP token generated.", extra={"email": email})
    _settings = get_settings()
    await EmailSender.from_settings(_settings).send(
        EmailTemplate.otp(to=email, otp_code=otp, portal_url=_settings.frontend_url)
    )


class IncorrectOtpError(Exception):
    """Raised when the supplied OTP value does not match the stored token hash."""


class TooManyAttemptsError(Exception):
    """Raised when the per-token failed-attempt limit has been reached."""


async def verify_otp(email: str, otp: str, session: AsyncSession) -> str:
    """Verify *otp* for the user identified by *email* and return a signed JWT on success.

    Raises:
        IncorrectOtpError: When the email has no active token or the OTP value is wrong.
        TooManyAttemptsError: When the token's failed-attempt limit is reached.

    The caller is responsible for mapping these exceptions to the appropriate
    HTTP responses (401 and 429 respectively).

    On a failed attempt the ``attempts`` counter is incremented atomically.
    When the counter reaches ``_MAX_OTP_ATTEMPTS`` the token is also marked as
    used so that it cannot be resubmitted after the limit message is shown.
    """
    user = await db_auth.get_user_by_email(session, email)
    if user is None or not user.is_active:
        logger.warning(
            "OTP verification attempted for unregistered or inactive address.",
            extra={"email": email},
        )
        raise IncorrectOtpError

    token = await db_auth.get_active_otp_token(session, user.id)
    if token is None:
        logger.warning(
            "No active OTP token found for user during verification.",
            extra={"email": email},
        )
        raise IncorrectOtpError

    if not bcrypt.checkpw(otp.encode(), token.token_hash.encode()):
        new_attempts = await db_auth.increment_otp_attempts(session, token.id)
        if new_attempts >= _MAX_OTP_ATTEMPTS:
            # Invalidate the token so it cannot be reused after the limit is reached.
            await db_auth.mark_otp_token_used(session, token.id)
            await session.commit()
            logger.warning(
                "OTP verification failed: attempt limit reached; token invalidated.",
                extra={"email": email},
            )
            raise TooManyAttemptsError
        await session.commit()
        logger.warning(
            "OTP verification failed: hash mismatch.",
            extra={"email": email, "attempts": new_attempts},
        )
        raise IncorrectOtpError

    # Hash matched — mark the token consumed and issue a JWT.
    await db_auth.mark_otp_token_used(session, token.id)
    await session.commit()

    logger.info("OTP verification succeeded; JWT issued.", extra={"email": email})
    return _create_jwt(user)
