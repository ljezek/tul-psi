from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from db.courses import create_course as db_create_course
from db.courses import get_course_by_code as db_get_course_by_code
from db.courses import update_course as db_update_course
from models.course import Course, CourseTerm, ProjectType
from schemas.courses import CourseCreate, CourseUpdate

# ---------------------------------------------------------------------------
# DB layer unit tests for courses write functions
# ---------------------------------------------------------------------------


async def test_get_course_by_code_returns_none_when_not_found() -> None:
    """``get_course_by_code`` must return ``None`` when no row matches the given code."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    session = AsyncMock()
    session.execute.return_value = mock_result

    result = await db_get_course_by_code(session, "NONEXISTENT")

    assert result is None


async def test_create_course_adds_to_session_and_flushes() -> None:
    """``create_course`` must add the new course to the session and flush."""
    session = MagicMock()
    session.flush = AsyncMock()

    data = CourseCreate(
        code="PSI",
        name="Projektový seminář informatiky",
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=50,
    )

    result = await db_create_course(session, data, created_by=1)

    session.add.assert_called_once()
    session.flush.assert_called_once()
    assert result.code == "PSI"
    assert result.name == "Projektový seminář informatiky"
    assert result.created_by == 1


async def test_create_course_sets_optional_fields() -> None:
    """``create_course`` must persist optional fields provided in the payload."""
    session = MagicMock()
    session.flush = AsyncMock()

    data = CourseCreate(
        code="OPT",
        name="Optional Fields Course",
        term=CourseTerm.SUMMER,
        project_type=ProjectType.INDIVIDUAL,
        min_score=40,
        syllabus="Course syllabus text.",
        peer_bonus_budget=5,
        evaluation_criteria=[{"code": "c1", "description": "Criterion 1", "max_score": 10}],
        links=[{"label": "eL", "url": "https://example.com"}],
    )

    result = await db_create_course(session, data, created_by=2)

    assert result.syllabus == "Course syllabus text."
    assert result.peer_bonus_budget == 5
    assert result.evaluation_criteria == [
        {"code": "c1", "description": "Criterion 1", "max_score": 10}
    ]
    assert result.links == [{"label": "eL", "url": "https://example.com"}]


async def test_update_course_applies_only_set_fields() -> None:
    """``update_course`` must update only the fields present in the payload."""
    session = MagicMock()
    session.flush = AsyncMock()

    course = MagicMock(spec=Course)
    course.code = "OLD"
    course.name = "Old Name"
    course.term = CourseTerm.WINTER

    data = CourseUpdate(name="New Name")

    result = await db_update_course(session, course, data)

    # Only 'name' should have been set; 'code' and 'term' remain unchanged.
    assert course.name == "New Name"
    session.add.assert_called_once_with(course)
    session.flush.assert_called_once()
    assert result is course


async def test_update_course_does_not_apply_unset_fields() -> None:
    """``update_course`` must not overwrite fields not present in the payload."""
    session = MagicMock()
    session.flush = AsyncMock()

    course = MagicMock(spec=Course)
    course.min_score = 60

    # Empty update — nothing should be touched.
    data = CourseUpdate()

    await db_update_course(session, course, data)

    # min_score must remain at its original value.
    assert course.min_score == 60


async def test_update_course_can_clear_nullable_field() -> None:
    """``update_course`` must allow setting a nullable field (e.g. syllabus) to None."""
    session = MagicMock()
    session.flush = AsyncMock()

    course = MagicMock(spec=Course)
    course.syllabus = "Existing syllabus."

    data = CourseUpdate(syllabus=None)

    await db_update_course(session, course, data)

    assert course.syllabus is None
