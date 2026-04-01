from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel

from models import Course, CourseTerm, ProjectType

# ---------------------------------------------------------------------------
# Course model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course() -> Course:
    return Course(
        code="PSI",
        name="Projektový seminář informatiky",
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=50,
    )


def test_course_create_minimal(sample_course: Course) -> None:
    """Course can be instantiated with only the required fields."""
    assert sample_course.code == "PSI"
    assert sample_course.name == "Projektový seminář informatiky"
    assert sample_course.term == CourseTerm.WINTER
    assert sample_course.project_type == ProjectType.TEAM
    assert sample_course.min_score == 50


def test_course_id_defaults_to_none(sample_course: Course) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_course.id is None


def test_course_optional_fields_default_to_none(sample_course: Course) -> None:
    """Nullable fields must default to None when not supplied."""
    assert sample_course.syllabus is None
    assert sample_course.peer_bonus_budget is None
    assert sample_course.created_by is None


def test_course_jsonb_fields_default_to_empty_list(sample_course: Course) -> None:
    """evaluation_criteria and links must default to [] so new instances are valid."""
    assert sample_course.evaluation_criteria == []
    assert sample_course.links == []


def test_course_jsonb_fields_accept_structured_data() -> None:
    """evaluation_criteria and links must accept their expected JSONB element shapes."""
    criteria = [{"code": "code_quality", "description": "Code Quality", "max_score": 25}]
    links = [{"label": "eLearning", "url": "https://elearning.tul.cz/"}]
    course = Course(
        code="PSI2",
        name="Test Course",
        term=CourseTerm.SUMMER,
        project_type=ProjectType.INDIVIDUAL,
        min_score=40,
        evaluation_criteria=criteria,
        links=links,
    )
    assert course.evaluation_criteria == criteria
    assert course.links == links


def test_course_evaluation_criteria_rejects_missing_keys() -> None:
    """evaluation_criteria items missing required keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD",
            name="Bad Course",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            # missing 'description' and 'max_score'
            evaluation_criteria=[{"code": "x"}],
        )


def test_course_evaluation_criteria_rejects_extra_keys() -> None:
    """evaluation_criteria items with unexpected extra keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD3",
            name="Bad Course 3",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            evaluation_criteria=[
                {"code": "x", "description": "X", "max_score": 10, "unknown_field": "nope"}
            ],
        )


def test_course_links_rejects_missing_keys() -> None:
    """links items missing required keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD2",
            name="Bad Course 2",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            # missing 'url'
            links=[{"label": "only label"}],
        )


def test_course_links_rejects_extra_keys() -> None:
    """links items with unexpected extra keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD4",
            name="Bad Course 4",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            links=[
                {"label": "eLearning", "url": "https://elearning.tul.cz/", "unknown_field": "nope"}
            ],
        )


def test_course_created_at_defaults_to_now() -> None:
    """created_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    course = Course(
        code="XYZ",
        name="X",
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=0,
    )
    after = datetime.now(UTC)
    assert before <= course.created_at <= after


def test_course_is_registered_in_metadata() -> None:
    """Course table must be present in SQLModel.metadata after import."""
    assert "course" in SQLModel.metadata.tables
