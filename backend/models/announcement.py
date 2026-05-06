from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class AnnouncementSeverity(str, enum.Enum):
    """Visual severity level for the announcement banner."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Announcement(SQLModel, table=True):
    """A system-wide notification message displayed to all users."""

    id: int | None = Field(default=None, primary_key=True)
    message: str = Field(max_length=1000)
    severity: AnnouncementSeverity = Field(default=AnnouncementSeverity.INFO)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
