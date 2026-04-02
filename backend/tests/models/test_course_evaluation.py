from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from models import CourseEvaluation

# ---------------------------------------------------------------------------
# CourseEvaluation model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course_evaluation() -> CourseEvaluation:
    return CourseEvaluation(project_id=1, student_id=3, rating=4)


def test_course_evaluation_create_minimal(
    sample_course_evaluation: CourseEvaluation,
) -> None:
    """CourseEvaluation can be instantiated with project_id, student_id, and rating."""
    assert sample_course_evaluation.project_id == 1
    assert sample_course_evaluation.student_id == 3
    assert sample_course_evaluation.rating == 4


def test_course_evaluation_default_fields(
    sample_course_evaluation: CourseEvaluation,
) -> None:
    """submitted, strengths, and improvements must default correctly.

    id must be None before the record is persisted to the database.
    """
    assert sample_course_evaluation.id is None
    assert sample_course_evaluation.submitted is False
    assert sample_course_evaluation.strengths is None
    assert sample_course_evaluation.improvements is None


def test_course_evaluation_rating_accepts_boundary_values() -> None:
    """rating must accept the boundary values 1 (min) and 5 (max) without error."""
    low = CourseEvaluation(project_id=1, student_id=1, rating=1)
    high = CourseEvaluation(project_id=1, student_id=2, rating=5)
    assert low.rating == 1
    assert high.rating == 5


def test_course_evaluation_rating_rejects_out_of_range() -> None:
    """rating values outside 1–5 must raise a ValidationError."""
    with pytest.raises(ValidationError):
        CourseEvaluation(project_id=1, student_id=1, rating=0)
    with pytest.raises(ValidationError):
        CourseEvaluation(project_id=1, student_id=1, rating=6)


def test_course_evaluation_updated_at_defaults_to_now() -> None:
    """updated_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    evaluation = CourseEvaluation(project_id=1, student_id=1, rating=3)
    after = datetime.now(UTC)
    assert before <= evaluation.updated_at <= after


def test_course_evaluation_is_registered_in_metadata() -> None:
    """course_evaluation table must be present in SQLModel.metadata after import."""
    assert "course_evaluation" in SQLModel.metadata.tables


def test_course_evaluation_rejects_duplicate_submission() -> None:
    """Inserting the same (project_id, student_id) pair twice must raise an IntegrityError."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.tables["course_evaluation"].create(engine)
    with Session(engine) as session:
        session.add(CourseEvaluation(project_id=1, student_id=1, rating=3))
        session.commit()
        session.add(CourseEvaluation(project_id=1, student_id=1, rating=4))
        with pytest.raises(IntegrityError):
            session.commit()
