from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy import DateTime as SADateTime
from sqlmodel import Field, SQLModel


class CourseLecturer(SQLModel, table=True):
    """Association between a course and a lecturer assigned to teach it.

    Uses a composite primary key ``(course_id, user_id)`` — the natural key
    for this relationship.  A lecturer can be assigned to multiple courses and
    a course can have multiple lecturers.
    """

    __tablename__: ClassVar[str] = "course_lecturer"

    # Composite primary key expressed via SQLModel's idiomatic primary_key=True
    # on each column so that the ORM identity key is known for session.get() /
    # session.merge() calls.  No surrogate id is needed for a pure join table.
    course_id: int = Field(primary_key=True, foreign_key="course.id")
    user_id: int = Field(primary_key=True, foreign_key="user.id")
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )
