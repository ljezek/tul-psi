from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.announcement import Announcement, AnnouncementSeverity


async def get_active_announcement(session: AsyncSession) -> Announcement | None:
    """Return the most recently updated active announcement, or ``None`` if absent."""
    result = await session.execute(
        select(Announcement)
        .where(Announcement.is_active == True)  # noqa: E712
        .order_by(Announcement.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_announcements(session: AsyncSession) -> list[Announcement]:
    """Return all announcements ordered by most recently updated first."""
    result = await session.execute(select(Announcement).order_by(Announcement.updated_at.desc()))
    return list(result.scalars().all())


async def get_announcement(session: AsyncSession, announcement_id: int) -> Announcement | None:
    """Return the announcement identified by *announcement_id*, or ``None`` if not found."""
    result = await session.execute(select(Announcement).where(Announcement.id == announcement_id))
    return result.scalar_one_or_none()


async def create_announcement(
    session: AsyncSession,
    *,
    message: str,
    severity: AnnouncementSeverity,
    is_active: bool,
) -> Announcement:
    """Persist a new announcement and return the refreshed ORM object."""
    announcement = Announcement(message=message, severity=severity, is_active=is_active)
    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)
    return announcement


async def update_announcement(
    session: AsyncSession,
    announcement: Announcement,
    *,
    message: str | None = None,
    severity: AnnouncementSeverity | None = None,
    is_active: bool | None = None,
) -> Announcement:
    """Apply partial updates to *announcement* and return the refreshed ORM object."""
    if message is not None:
        announcement.message = message
    if severity is not None:
        announcement.severity = severity
    if is_active is not None:
        announcement.is_active = is_active
    announcement.updated_at = datetime.now(UTC)
    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)
    return announcement


async def delete_announcement(session: AsyncSession, announcement: Announcement) -> None:
    """Delete *announcement* from the database."""
    await session.delete(announcement)
    await session.commit()
