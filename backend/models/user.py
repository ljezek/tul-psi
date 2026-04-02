from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Boolean, Column, Enum
from sqlalchemy import DateTime as SADateTime
from sqlmodel import Field, SQLModel


class UserRole(str, enum.Enum):
    """Roles that can be assigned to a user account."""

    ADMIN = "ADMIN"
    LECTURER = "LECTURER"
    STUDENT = "STUDENT"


class User(SQLModel, table=True):
    """Registered user of the Student Projects Catalogue.

    ``role`` controls which parts of the application a user can access:
    ADMIN may manage courses and users; LECTURER manages projects and
    evaluations; STUDENT edits their own project and submits peer feedback.

    Note: ``user`` is a reserved word in PostgreSQL — SQLAlchemy (and therefore
    Alembic) will automatically quote the identifier in generated DDL.
    """

    __tablename__: ClassVar[str] = "user"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    github_alias: str | None = Field(default=None, max_length=100)
    name: str = Field(max_length=255)
    role: UserRole = Field(sa_column=Column(Enum(UserRole), nullable=False))
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )
