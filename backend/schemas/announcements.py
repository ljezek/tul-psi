from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models.announcement import AnnouncementSeverity


class AnnouncementPublic(BaseModel):
    """Public representation of an announcement returned by the API."""

    model_config = {"from_attributes": True}

    id: int
    message: str
    severity: AnnouncementSeverity
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AnnouncementCreate(BaseModel):
    """Payload for creating a new announcement."""

    message: str = Field(min_length=1, max_length=1000)
    severity: AnnouncementSeverity = AnnouncementSeverity.INFO
    is_active: bool = False


class AnnouncementUpdate(BaseModel):
    """Partial update payload for an existing announcement."""

    message: str | None = Field(default=None, min_length=1, max_length=1000)
    severity: AnnouncementSeverity | None = None
    is_active: bool | None = None
