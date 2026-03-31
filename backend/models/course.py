from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import ClassVar, TypedDict

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


class EvaluationCriterion(TypedDict):
    """Shape of a single evaluation criterion stored in Course.evaluation_criteria."""

    code: str  # short immutable identifier; used as key in PROJECT_EVALUATION.scores
    description: str  # human-readable label shown in the UI
    max_score: int  # maximum points a student can receive for this criterion


class CourseLink(TypedDict):
    """Shape of a single link stored in Course.links."""

    label: str  # human-readable link text shown in the UI
    url: str  # absolute URL


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
    # null means no peer-bonus-point scheme for this course
    peer_bonus_budget: int | None = Field(default=None)
    # JSONB array of EvaluationCriterion elements
    evaluation_criteria: list[EvaluationCriterion] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    # JSONB array of CourseLink elements
    links: list[CourseLink] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    created_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __init__(self, **data: object) -> None:
        # SQLModel 0.0.x bypasses Pydantic validators for table=True models, so
        # we validate the JSONB fields explicitly before delegating to SQLModel.
        _validate_evaluation_criteria(data.get("evaluation_criteria") or [])
        _validate_links(data.get("links") or [])
        super().__init__(**data)


def _validate_evaluation_criteria(value: object) -> None:
    """Raise ValueError if any criterion is missing required keys or has wrong types."""
    if not isinstance(value, list):
        raise ValueError("evaluation_criteria must be a list")
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("each criterion must be a mapping")
        missing = {"code", "description", "max_score"} - item.keys()
        if missing:
            raise ValueError(f"criterion is missing required keys: {missing}")
        if not isinstance(item["max_score"], int):
            raise ValueError("max_score must be an integer")


def _validate_links(value: object) -> None:
    """Raise ValueError if any link is missing required keys."""
    if not isinstance(value, list):
        raise ValueError("links must be a list")
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("each link must be a mapping")
        missing = {"label", "url"} - item.keys()
        if missing:
            raise ValueError(f"link is missing required keys: {missing}")
