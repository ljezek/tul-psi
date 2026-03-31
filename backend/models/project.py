from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    """A student project associated with a course and academic year.

    ``technologies`` is stored as a JSONB array of plain strings, e.g.::

        ["Python", "FastAPI", "React"]

    ``results_unlocked`` controls whether students can see their evaluation
    results; it is set to ``True`` by a lecturer after all evaluations are in.
    """

    __tablename__: ClassVar[str] = "project"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None)
    github_url: str | None = Field(default=None, max_length=500)
    live_url: str | None = Field(default=None, max_length=500)
    # JSONB array of technology name strings
    technologies: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    results_unlocked: bool = Field(default=False)
    course_id: int = Field(foreign_key="course.id")
    # e.g. 2025 — the academic year the project was submitted
    academic_year: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
