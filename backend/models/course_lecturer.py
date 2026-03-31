from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import PrimaryKeyConstraint
from sqlmodel import Field, SQLModel


class CourseLecturer(SQLModel, table=True):
    """Association between a course and a lecturer assigned to teach it.

    Uses a composite primary key ``(course_id, user_id)`` — the natural key
    for this relationship.  A lecturer can be assigned to multiple courses and
    a course can have multiple lecturers.
    """

    __tablename__: ClassVar[str] = "course_lecturer"
    # Composite primary key; no surrogate id is needed for a pure join table.
    __table_args__: ClassVar[tuple] = (
        PrimaryKeyConstraint("course_id", "user_id", name="pk_course_lecturer"),
    )

    course_id: int = Field(foreign_key="course.id")
    user_id: int = Field(foreign_key="user.id")
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
