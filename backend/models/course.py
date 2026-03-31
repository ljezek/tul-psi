from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class CourseTerm(str, enum.Enum):
    """Academic term in which a course is offered."""

    SUMMER = "SUMMER"
    WINTER = "WINTER"


class ProjectType(str, enum.Enum):
    """Whether projects in a course are collaborative or individual."""

    TEAM = "TEAM"
    INDIVIDUAL = "INDIVIDUAL"


class Course(SQLModel, table=True):
    """A course offered in a given academic term.

    ``evaluation_criteria`` and ``links`` are stored as JSONB so that their
    shape can evolve without schema migrations.

    Expected ``evaluation_criteria`` format::

        [{"code": "code_quality", "description": "Code Quality", "max_score": 25}]

    Expected ``links`` format::

        [{"label": "eLearning", "url": "https://elearning.tul.cz/..."}]
    """

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=255)
    syllabus: str | None = Field(default=None)
    term: CourseTerm
    project_type: ProjectType
    min_score: int
    # null means no peer-bonus-point scheme for this course
    peer_bonus_budget: int | None = Field(default=None)
    # JSONB — see class docstring for the expected element shape
    evaluation_criteria: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    links: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    created_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Explicit table name keeps it consistent with the entity diagram in DESIGN.md.
    __tablename__: ClassVar[str] = "course"
