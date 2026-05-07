from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_current_user
from db.session import get_session
from models.user import User
from schemas.announcements import AnnouncementCreate, AnnouncementPublic, AnnouncementUpdate
from services.announcements import (
    AnnouncementNotFoundError,
    AnnouncementsService,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/announcements", tags=["announcements"])


def get_announcements_service(session: AsyncSession = Depends(get_session)) -> AnnouncementsService:
    """Provide an ``AnnouncementsService`` instance wired to the current DB session."""
    return AnnouncementsService(session)


@router.get(
    "/active",
    response_model=AnnouncementPublic | None,
    summary="Get active announcement",
    description="Returns the currently active announcement, or null if none exists.",
)
async def get_active_announcement(
    service: AnnouncementsService = Depends(get_announcements_service),
) -> AnnouncementPublic | None:
    """Return the active announcement for display to all users, including unauthenticated visitors.

    This is a public endpoint — no authentication is required.
    """
    return await service.get_active()


@router.get(
    "",
    response_model=list[AnnouncementPublic],
    summary="List all announcements (admin only)",
)
async def get_all_announcements(
    current_user: User = Depends(require_current_user),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> list[AnnouncementPublic]:
    """Return all announcements. Restricted to admins."""
    try:
        return await service.get_all(current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "",
    response_model=AnnouncementPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create an announcement (admin only)",
)
async def create_announcement(
    body: AnnouncementCreate,
    current_user: User = Depends(require_current_user),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> AnnouncementPublic:
    """Create a new announcement. Restricted to admins."""
    try:
        return await service.create(body, current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.patch(
    "/{announcement_id}",
    response_model=AnnouncementPublic,
    summary="Update an announcement (admin only)",
)
async def update_announcement(
    announcement_id: int,
    body: AnnouncementUpdate,
    current_user: User = Depends(require_current_user),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> AnnouncementPublic:
    """Partially update an existing announcement. Restricted to admins."""
    try:
        return await service.update(announcement_id, body, current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AnnouncementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete an announcement (admin only)",
)
async def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(require_current_user),
    service: AnnouncementsService = Depends(get_announcements_service),
) -> None:
    """Delete an announcement. Restricted to admins."""
    try:
        await service.delete(announcement_id, current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AnnouncementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
