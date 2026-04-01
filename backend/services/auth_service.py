from __future__ import annotations

import logging
import random
import string

import bcrypt
from sqlalchemy import not_, update
from sqlmodel import Session, select

from models import OtpToken, User

logger = logging.getLogger(__name__)


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


def request_otp(email: str, session: Session) -> None:
    """Generate an OTP for *email* and persist its hash in the database.

    The response is deliberately identical whether or not the email is
    registered; this prevents user-enumeration attacks (see DESIGN.md).

    Any previously active (non-used) tokens for the user are invalidated before
    the new token is inserted to prevent token accumulation and limit the attack
    surface if an earlier code was intercepted.

    The plaintext OTP is written to the application log instead of being sent
    via SMTP.

    # TODO: Replace the log statement below with a real SMTP email delivery
    # once an email sending service (e.g., SendGrid, Azure Communication
    # Services) is integrated.
    """
    user = session.exec(select(User).where(User.email == email)).first()

    if user is None:
        # Silent success — do not reveal that the address is not registered.
        logger.warning(
            "OTP requested for unregistered address; no token created.",
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

    # Invalidate all active tokens for this user with a single bulk UPDATE.
    # This runs in the same transaction as the new token insert below; if any
    # subsequent step fails, the whole unit of work is rolled back together.
    session.exec(
        update(OtpToken).values(used=True).where(OtpToken.user_id == user.id, not_(OtpToken.used))
    )

    otp = _generate_otp()
    token = OtpToken(user_id=user.id, token_hash=_hash_otp(otp))
    session.add(token)
    session.commit()

    # TODO: Send the OTP via SMTP instead of logging it.
    logger.info("OTP generated: %s", otp, extra={"email": email})
