from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import DateTime as SADateTime
from sqlmodel import Field, SQLModel


class ProjectMember(SQLModel, table=True):
    """Association between a user and a project (team membership).

    A row is created when a lecturer seeds a new project (for the owner) or
    when an existing member adds another student by e-mail.  ``joined_at`` is
    ``None`` until the invited student accepts the invitation.
    """

    __tablename__: ClassVar[str] = "project_member"
    # A user can only be a member of a given project once.
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member_project_user"),
    )

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    user_id: int = Field(foreign_key="user.id")
    # Null means the member was seeded directly (e.g. the initial project owner).
    invited_by: int | None = Field(default=None, foreign_key="user.id")
    invited_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )
    # Null until the invitation is accepted.
    joined_at: datetime | None = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), nullable=True),
    )
