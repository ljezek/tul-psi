from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import not_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models import OtpToken, User
from models.user import UserRole


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Return the User row matching *email*, or None if no such user exists."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_or_create_user(
    session: AsyncSession,
    email: str,
    name: str | None = None,
    github_alias: str | None = None,
) -> tuple[User, bool]:
    """Return the user matching *email*, creating a new STUDENT account if absent.

    Uses an UPSERT (INSERT … ON CONFLICT DO NOTHING) so concurrent requests
    for the same address are handled atomically without a separate SELECT before
    INSERT.  *name* and *github_alias* are only used when a new row is created;
    callers are responsible for computing any desired defaults (e.g. deriving
    a display name from the local part of the e-mail address).

    Returns a ``(user, created)`` tuple where ``created`` is ``True`` when a new
    row was inserted and ``False`` when an existing row was returned.
    The caller must commit the session after a successful return.
    """
    stmt = (
        pg_insert(User)
        .values(
            email=email,
            name=name,
            github_alias=github_alias,
            role=UserRole.STUDENT,
            created_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(index_elements=["email"])
    )
    result = await session.execute(stmt)
    created = result.rowcount > 0
    # Fetch the full ORM object whether just inserted or pre-existing.
    user = (await session.execute(select(User).where(User.email == email))).scalars().first()
    if user is None:
        raise RuntimeError(f"Expected user row for {email!r} after UPSERT.")
    return user, created


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Return the User row matching *user_id*, or None if no such user exists."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def invalidate_active_otp_tokens(session: AsyncSession, user_id: int) -> None:
    """Mark all non-used OTP tokens for *user_id* as used.

    Runs as part of the same transaction as the subsequent token insert; if any
    later step fails the whole unit of work is rolled back together.
    """
    await session.execute(
        update(OtpToken)
        .values(used=True)
        .where(
            OtpToken.user_id == user_id,
            not_(OtpToken.used),
        )
    )


def add_otp_token(session: AsyncSession, token: OtpToken) -> None:
    """Stage *token* for insertion into the database.

    Does not commit — the caller is responsible for calling ``session.commit()``
    after all related changes have been staged so they are written atomically.
    """
    session.add(token)


async def get_active_otp_token(session: AsyncSession, user_id: int) -> OtpToken | None:
    """Return the most recent non-used, non-expired OTP token for *user_id*.

    Returns ``None`` when no such token exists (never issued, already used,
    or all tokens have expired).
    """
    now = datetime.now(UTC)
    result = await session.execute(
        select(OtpToken)
        .where(
            OtpToken.user_id == user_id,
            not_(OtpToken.used),
            OtpToken.expires_at > now,
        )
        .order_by(OtpToken.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def increment_otp_attempts(session: AsyncSession, token_id: int) -> int:
    """Increment the failed-attempt counter for token *token_id*.

    Returns the new attempts count so callers can enforce the per-token limit
    without an additional SELECT.
    """
    result = await session.execute(
        update(OtpToken)
        .values(attempts=OtpToken.attempts + 1)
        .where(OtpToken.id == token_id)
        .returning(OtpToken.attempts)
    )
    new_attempts: int = result.scalar_one()
    return new_attempts


async def mark_otp_token_used(session: AsyncSession, token_id: int) -> None:
    """Set the ``used`` flag on the token identified by *token_id*.

    Prevents the same token from being accepted a second time.
    """
    await session.execute(update(OtpToken).values(used=True).where(OtpToken.id == token_id))
