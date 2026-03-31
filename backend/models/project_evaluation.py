from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar, TypedDict

from pydantic import TypeAdapter
from pydantic.config import ConfigDict
from sqlalchemy import Column
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class EvaluationScore(TypedDict):
    """Shape of a single per-criterion score stored in ProjectEvaluation.scores.

    ``criterion_code`` references a ``code`` value from the parent
    ``Course.evaluation_criteria`` list.  ``strengths`` and ``improvements``
    are required narrative fields — the API spec does not allow partial
    submissions without text.
    """

    __pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore[assignment]

    criterion_code: str  # Matches EvaluationCriterion.code on the parent Course.
    score: int  # Points awarded; must not exceed EvaluationCriterion.max_score.
    strengths: str  # Positive feedback narrative for this criterion.
    improvements: str  # Constructive feedback narrative for this criterion.


# Module-level adapter built once; reused on every ProjectEvaluation instantiation.
_scores_adapter: TypeAdapter[list[EvaluationScore]] = TypeAdapter(list[EvaluationScore])


class ProjectEvaluation(SQLModel, table=True):
    """Lecturer evaluation of a single project.

    Each assigned lecturer submits exactly one row per project; the pair
    ``(project_id, lecturer_id)`` is therefore unique.  Final scores visible
    to students are the average across all submitted ``ProjectEvaluation`` rows
    for a given project.
    """

    __tablename__: ClassVar[str] = "project_evaluation"

    # Composite primary key expressed via SQLModel's idiomatic primary_key=True on each column.
    # No surrogate id is needed; the natural key uniquely identifies the row.
    project_id: int = Field(primary_key=True, foreign_key="project.id")
    lecturer_id: int = Field(primary_key=True, foreign_key="user.id")
    # JSONB array of EvaluationScore elements — one entry per criterion.
    scores: list[EvaluationScore] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )

    def __init__(self, **data: object) -> None:
        # SQLModel 0.0.x bypasses Pydantic validators for table=True models, so
        # we validate the JSONB field explicitly before delegating to SQLModel.
        _scores_adapter.validate_python(data.get("scores") or [])
        super().__init__(**data)
