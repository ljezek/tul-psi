from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Return the user identified by *user_id* or ``None`` if not found."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_users(session: AsyncSession) -> list[User]:
    """Return all users in the system."""
    result = await session.execute(select(User).order_by(User.id))
    return list(result.scalars().all())
