from __future__ import annotations

import logging
import random
import string

import bcrypt
from sqlmodel import Session, select

from models import OtpToken, User

logger = logging.getLogger(__name__)


def _generate_otp() -> str:
    """Return a cryptographically random 6-digit numeric OTP string."""
    return "".join(random.SystemRandom().choices(string.digits, k=6))


def _hash_otp(otp: str) -> str:
    """Return a bcrypt hash of *otp* encoded as a UTF-8 string.

    A fresh salt is generated for every call so each token hash is unique.
    """
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def request_otp(email: str, session: Session) -> None:
    """Generate an OTP for *email* and persist its hash in the database.

    The response is deliberately identical whether or not the email is
    registered; this prevents user-enumeration attacks (see DESIGN.md).

    The plaintext OTP is written to the application log instead of being
    sent via SMTP.

    # TODO: Replace the log statement below with a real SMTP email delivery
    # once an email sending service (e.g., SendGrid, Azure Communication
    # Services) is integrated.
    """
    user = session.exec(select(User).where(User.email == email)).first()

    if user is None:
        # Silent success — do not reveal that the address is not registered.
        logger.info("OTP requested for unregistered address; no token created.")
        return

    if user.id is None:
        # Guard against a partially-constructed object that was never persisted.
        logger.warning("User record has no primary key; OTP generation skipped.")
        return

    otp = _generate_otp()
    token = OtpToken(user_id=user.id, token_hash=_hash_otp(otp))
    session.add(token)
    session.commit()

    # TODO: Send the OTP via SMTP instead of logging it.
    logger.info("OTP for %s: %s", email, otp)
