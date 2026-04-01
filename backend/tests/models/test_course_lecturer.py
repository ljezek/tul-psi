from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from models import CourseLecturer

# ---------------------------------------------------------------------------
# CourseLecturer model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course_lecturer() -> CourseLecturer:
    return CourseLecturer(course_id=1, user_id=5)


def test_course_lecturer_create_minimal(sample_course_lecturer: CourseLecturer) -> None:
    """CourseLecturer can be instantiated with only course_id and user_id."""
    assert sample_course_lecturer.course_id == 1
    assert sample_course_lecturer.user_id == 5


def test_course_lecturer_assigned_at_defaults_to_now() -> None:
    """assigned_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    cl = CourseLecturer(course_id=1, user_id=5)
    after = datetime.now(UTC)
    assert before <= cl.assigned_at <= after


def test_course_lecturer_is_registered_in_metadata() -> None:
    """course_lecturer table must be present in SQLModel.metadata after import."""
    assert "course_lecturer" in SQLModel.metadata.tables


def test_course_lecturer_rejects_duplicate_assignment() -> None:
    """Inserting the same (course_id, user_id) pair twice must raise an IntegrityError."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.tables["course_lecturer"].create(engine)
    with Session(engine) as session:
        session.add(CourseLecturer(course_id=1, user_id=5))
        session.commit()
        session.add(CourseLecturer(course_id=1, user_id=5))
        with pytest.raises(IntegrityError):
            session.commit()
