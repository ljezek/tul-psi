from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import ClassVar, TypedDict

from pydantic import TypeAdapter
from pydantic.config import ConfigDict
from sqlalchemy import Column
from sqlalchemy import DateTime as SADateTime
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


class EvaluationCriterion(TypedDict):
    """Shape of a single evaluation criterion stored in Course.evaluation_criteria."""

    __pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore[assignment]

    code: str  # Short immutable identifier; used as key in PROJECT_EVALUATION.scores.
    description: str  # Human-readable label shown in the UI.
    max_score: int  # Maximum points a student can receive for this criterion.


class CourseLink(TypedDict):
    """Shape of a single link stored in Course.links."""

    __pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore[assignment]

    label: str  # Human-readable link text shown in the UI.
    url: str  # Absolute URL.


# Module-level adapters built once; reused on every Course instantiation.
_criteria_adapter: TypeAdapter[list[EvaluationCriterion]] = TypeAdapter(list[EvaluationCriterion])
_links_adapter: TypeAdapter[list[CourseLink]] = TypeAdapter(list[CourseLink])


class Course(SQLModel, table=True):
    """A course offered in a given academic term."""

    __tablename__: ClassVar[str] = "course"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=255)
    syllabus: str | None = Field(default=None)
    term: CourseTerm
    project_type: ProjectType
    min_score: int
    # Null means no peer-bonus-point scheme for this course.
    peer_bonus_budget: int | None = Field(default=None)
    # JSONB array of EvaluationCriterion elements.
    evaluation_criteria: list[EvaluationCriterion] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    # JSONB array of CourseLink elements.
    links: list[CourseLink] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    created_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )

    def __init__(self, **data: object) -> None:
        # SQLModel 0.0.x bypasses Pydantic validators for table=True models, so
        # we validate the JSONB fields explicitly before delegating to SQLModel.
        _criteria_adapter.validate_python(data.get("evaluation_criteria") or [])
        _links_adapter.validate_python(data.get("links") or [])
        super().__init__(**data)
