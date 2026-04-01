from __future__ import annotations

import logging
import random
import string
import sys

import bcrypt
from sqlmodel import Session

from db import auth as db_auth
from models import OtpToken
from settings import get_settings

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

    # TODO: Replace the ``show_otp_dev_only`` fallback below with real SMTP email delivery
    # once an email sending service (e.g., SendGrid, Azure Communication
    # Services) is integrated.
    """
    user = db_auth.get_user_by_email(session, email)

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

    db_auth.invalidate_active_otp_tokens(session, user.id)

    otp = _generate_otp()
    token = OtpToken(user_id=user.id, token_hash=_hash_otp(otp))
    db_auth.add_otp_token(session, token)
    # Commit here — this is the full unit of work: invalidate old tokens and
    # insert the new one must succeed or fail together.
    session.commit()

    logger.info("OTP token generated.", extra={"email": email})
    if get_settings().show_otp_dev_only:
        # Dev-only fallback: print OTP to stderr when SMTP is not yet configured.
        # Do not enable show_otp_dev_only in production — it exposes the secret to anyone
        # with log/stderr access and defeats the purpose of the OTP.
        logger.warning(
            "show_otp_dev_only is enabled; plaintext OTP will be printed to stderr.",
            extra={"email": email},
        )
        print(f"[DEV] OTP for {email}: {otp}", file=sys.stderr)  # noqa: T201
