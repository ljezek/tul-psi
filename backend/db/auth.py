from __future__ import annotations

from sqlalchemy import not_, update
from sqlmodel import Session, select

from models import OtpToken, User


def get_user_by_email(session: Session, email: str) -> User | None:
    """Return the User row matching *email*, or None if no such user exists."""
    return session.exec(select(User).where(User.email == email)).first()


def invalidate_active_otp_tokens(session: Session, user_id: int) -> None:
    """Mark all non-used OTP tokens for *user_id* as used.

    Runs as part of the same transaction as the subsequent token insert; if any
    later step fails the whole unit of work is rolled back together.
    """
    session.exec(
        update(OtpToken)
        .values(used=True)
        .where(
            OtpToken.user_id == user_id,
            not_(OtpToken.used),
        )
    )


def add_otp_token(session: Session, token: OtpToken) -> None:
    """Stage *token* for insertion into the database.

    Does not commit — the caller is responsible for calling ``session.commit()``
    after all related changes have been staged so they are written atomically.
    """
    session.add(token)
