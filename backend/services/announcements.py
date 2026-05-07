from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from db.announcements import create_announcement as db_create_announcement
from db.announcements import delete_announcement as db_delete_announcement
from db.announcements import get_active_announcement as db_get_active_announcement
from db.announcements import get_announcement as db_get_announcement
from db.announcements import get_announcements as db_get_announcements
from db.announcements import update_announcement as db_update_announcement
from models.user import User, UserRole
from schemas.announcements import AnnouncementCreate, AnnouncementPublic, AnnouncementUpdate

logger = logging.getLogger(__name__)


class AnnouncementNotFoundError(Exception):
    """Raised when the requested announcement does not exist."""


class PermissionDeniedError(Exception):
    """Raised when a non-admin user attempts an admin-only operation."""


class AnnouncementsService:
    """Business logic for system-wide announcement management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self) -> AnnouncementPublic | None:
        """Return the currently active announcement, or ``None`` if none is active."""
        announcement = await db_get_active_announcement(self._session)
        if announcement is None:
            return None
        return AnnouncementPublic.model_validate(announcement)

    async def get_all(self, current_user: User) -> list[AnnouncementPublic]:
        """Return all announcements ordered by most recently updated. Restricted to admins."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can list all announcements.")
        announcements = await db_get_announcements(self._session)
        return [AnnouncementPublic.model_validate(a) for a in announcements]

    async def create(self, body: AnnouncementCreate, current_user: User) -> AnnouncementPublic:
        """Create and persist a new announcement. Restricted to admins."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can create announcements.")
        announcement = await db_create_announcement(
            self._session,
            message=body.message,
            severity=body.severity,
            is_active=body.is_active,
        )
        logger.info(
            "Announcement created.",
            extra={"announcement_id": announcement.id, "admin_id": current_user.id},
        )
        return AnnouncementPublic.model_validate(announcement)

    async def update(
        self,
        announcement_id: int,
        body: AnnouncementUpdate,
        current_user: User,
    ) -> AnnouncementPublic:
        """Partially update an existing announcement. Restricted to admins."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can update announcements.")
        announcement = await db_get_announcement(self._session, announcement_id)
        if announcement is None:
            raise AnnouncementNotFoundError(f"Announcement {announcement_id} not found.")
        updated = await db_update_announcement(
            self._session,
            announcement,
            message=body.message,
            severity=body.severity,
            is_active=body.is_active,
        )
        logger.info(
            "Announcement updated.",
            extra={"announcement_id": announcement_id, "admin_id": current_user.id},
        )
        return AnnouncementPublic.model_validate(updated)

    async def delete(self, announcement_id: int, current_user: User) -> None:
        """Delete an announcement. Restricted to admins."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can delete announcements.")
        announcement = await db_get_announcement(self._session, announcement_id)
        if announcement is None:
            raise AnnouncementNotFoundError(f"Announcement {announcement_id} not found.")
        await db_delete_announcement(self._session, announcement)
        logger.info(
            "Announcement deleted.",
            extra={"announcement_id": announcement_id, "admin_id": current_user.id},
        )
