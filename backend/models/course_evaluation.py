from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, ClassVar

from pydantic import Field as PydanticField, TypeAdapter
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import DateTime as SADateTime
from sqlmodel import Field, SQLModel


# Module-level adapter built once; enforces the 1–5 rating range on every
# CourseEvaluation instantiation without duplicating the constraint in the field.
_rating_adapter: TypeAdapter[Annotated[int, PydanticField(ge=1, le=5)]] = TypeAdapter(
    Annotated[int, PydanticField(ge=1, le=5)]
)


class CourseEvaluation(SQLModel, table=True):
    """Student evaluation of the course experience for a given project.

    A student submits one evaluation per project; the pair
    ``(project_id, student_id)`` is therefore unique.  The evaluation can be
    saved as a draft (``published=False``) any number of times before being
    locked by setting ``published=True``.  Peer feedback rows are children of
    this record via ``course_evaluation_id``.
    """

    __tablename__: ClassVar[str] = "course_evaluation"
    # A student may submit one evaluation per project.
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint(
            "project_id",
            "student_id",
            name="uq_course_evaluation_project_student",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    student_id: int = Field(foreign_key="user.id")
    # Overall course satisfaction rating; validated to the 1–5 range in __init__.
    rating: int
    # Null means the student has not yet filled in the free-text sections (draft).
    strengths: str | None = Field(default=None)
    improvements: str | None = Field(default=None)
    # Once published the evaluation is locked and cannot be edited further.
    published: bool = Field(default=False)
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )

    def __init__(self, **data: object) -> None:
        # SQLModel 0.0.x bypasses Pydantic validators for table=True models, so
        # we validate the rating field explicitly before delegating to SQLModel.
        if "rating" in data:
            _rating_adapter.validate_python(data["rating"])
        super().__init__(**data)
