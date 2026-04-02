from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole


async def get_or_create_user(
    session: AsyncSession,
    email: str,
    name: str | None = None,
    github_alias: str | None = None,
    role: UserRole = UserRole.STUDENT,
) -> tuple[User, bool]:
    """Return the user matching *email*, creating a new account if absent.

    Uses an UPSERT (INSERT … ON CONFLICT DO NOTHING) so concurrent requests
    for the same address are handled atomically without a separate SELECT before
    INSERT.  *name*, *github_alias*, and *role* are only used when a new row is
    created; callers are responsible for computing any desired defaults (e.g.
    deriving a display name from the local part of the e-mail address).

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
            role=role,
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


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Return the user identified by *user_id* or ``None`` if not found."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_users(session: AsyncSession) -> list[User]:
    """Return all users in the system."""
    result = await session.execute(select(User).order_by(User.id))
    return list(result.scalars().all())
