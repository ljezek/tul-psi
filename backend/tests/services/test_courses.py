from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.course import Course, CourseTerm, ProjectType
from models.course_evaluation import CourseEvaluation
from models.user import User, UserRole
from services.courses import CoursesService

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_course(course_id: int = 1) -> MagicMock:
    """Return a minimal mock ``Course`` row."""
    course = MagicMock(spec=Course)
    course.id = course_id
    course.code = "PSI"
    course.name = "Projektový seminář informatiky"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = ProjectType.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []
    return course


def _make_lecturer(user_id: int, email: str = "lecturer@tul.cz") -> MagicMock:
    """Return a mock ``User`` with the LECTURER role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.name = f"Lecturer {user_id}"
    user.email = email
    user.github_alias = None
    user.role = UserRole.LECTURER
    return user


def _make_evaluation(ev_id: int = 1) -> MagicMock:
    """Return a minimal mock ``CourseEvaluation`` row."""
    ev = MagicMock(spec=CourseEvaluation)
    ev.id = ev_id
    ev.project_id = 10
    ev.student_id = 5
    ev.rating = 4
    ev.strengths = "Good."
    ev.improvements = "Better."
    ev.published = True
    ev.submitted_at = datetime(2025, 1, 15, 12, 0, tzinfo=UTC)
    return ev


# ---------------------------------------------------------------------------
# CoursesService.get_course — role-based access to course_evaluations
# ---------------------------------------------------------------------------


async def test_owning_lecturer_receives_course_evaluations() -> None:
    """A lecturer who is assigned to the course must receive ``course_evaluations``."""
    course = _make_course(course_id=1)
    lecturer = _make_lecturer(user_id=42)
    evaluation = _make_evaluation()

    # The calling user is the lecturer who owns this course.
    current_user = MagicMock(spec=User)
    current_user.id = 42
    current_user.role = UserRole.LECTURER

    session = MagicMock()
    with (
        patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [lecturer]},
        ),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
            return_value=[evaluation],
        ) as mock_get_evals,
    ):
        result = await CoursesService(session).get_course(1, current_user=current_user)

    assert result is not None
    assert result.course_evaluations is not None
    assert len(result.course_evaluations) == 1
    assert result.course_evaluations[0].id == 1
    mock_get_evals.assert_called_once()


async def test_non_owning_lecturer_does_not_receive_course_evaluations() -> None:
    """A lecturer who is NOT assigned to the course must not receive ``course_evaluations``."""
    course = _make_course(course_id=1)
    # The course is owned by lecturer id=42, not by the calling user.
    owner_lecturer = _make_lecturer(user_id=42)

    # The calling user is a different lecturer with a different id.
    current_user = MagicMock(spec=User)
    current_user.id = 99
    current_user.role = UserRole.LECTURER

    session = MagicMock()
    with (
        patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [owner_lecturer]},
        ),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
        ) as mock_get_evals,
    ):
        result = await CoursesService(session).get_course(1, current_user=current_user)

    assert result is not None
    assert result.course_evaluations is None
    # The DB query must not be called for an unauthorised user.
    mock_get_evals.assert_not_called()


async def test_student_does_not_receive_course_evaluations() -> None:
    """A student must not receive ``course_evaluations`` regardless of course ownership."""
    course = _make_course(course_id=1)
    lecturer = _make_lecturer(user_id=42)

    current_user = MagicMock(spec=User)
    current_user.id = 5
    current_user.role = UserRole.STUDENT

    session = MagicMock()
    with (
        patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [lecturer]},
        ),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
        ) as mock_get_evals,
    ):
        result = await CoursesService(session).get_course(1, current_user=current_user)

    assert result is not None
    assert result.course_evaluations is None
    # The DB query must not be called for an unauthorised user.
    mock_get_evals.assert_not_called()


# ---------------------------------------------------------------------------
# CoursesService.get_courses — list assembly
# ---------------------------------------------------------------------------


async def test_get_courses_returns_empty_list_when_no_rows() -> None:
    """``get_courses`` must return an empty list when the DB has no courses."""
    session = MagicMock()
    with (
        patch("services.courses.db_get_courses", new_callable=AsyncMock, return_value=[]),
        patch(
            "services.courses.get_course_project_stats",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        result = await CoursesService(session).get_courses()

    assert result == []


async def test_get_courses_assembles_list_item() -> None:
    """``get_courses`` must build a ``CourseListItem`` with stats and sorted lecturer names."""
    course = _make_course(course_id=1)
    lecturer_a = _make_lecturer(user_id=10)
    lecturer_a.name = "Zuzana Nováková"
    lecturer_b = _make_lecturer(user_id=11)
    lecturer_b.name = "Adam Dvořák"

    session = MagicMock()
    with (
        patch(
            "services.courses.db_get_courses",
            new_callable=AsyncMock,
            return_value=[course],
        ),
        patch(
            "services.courses.get_course_project_stats",
            new_callable=AsyncMock,
            return_value={1: (5, [2023, 2024])},
        ),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [lecturer_a, lecturer_b]},
        ),
    ):
        result = await CoursesService(session).get_courses()

    assert len(result) == 1
    item = result[0]
    assert item.id == 1
    assert item.code == "PSI"
    # Lecturer names must be sorted alphabetically.
    assert item.lecturer_names == ["Adam Dvořák", "Zuzana Nováková"]
    assert item.stats.project_count == 5
    assert item.stats.academic_years == [2023, 2024]


async def test_get_courses_defaults_stats_for_course_with_no_projects() -> None:
    """``get_courses`` must use default (0, []) stats for courses absent from the stats map."""
    course = _make_course(course_id=7)

    session = MagicMock()
    with (
        patch(
            "services.courses.db_get_courses",
            new_callable=AsyncMock,
            return_value=[course],
        ),
        patch(
            "services.courses.get_course_project_stats",
            new_callable=AsyncMock,
            return_value={},  # No entry for course id 7.
        ),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        result = await CoursesService(session).get_courses()

    assert len(result) == 1
    assert result[0].stats.project_count == 0
    assert result[0].stats.academic_years == []


# ---------------------------------------------------------------------------
# CoursesService.get_course — lecturer email gating
# ---------------------------------------------------------------------------


async def test_authenticated_caller_receives_lecturer_email() -> None:
    """Any authenticated caller must receive lecturer e-mail addresses."""
    course = _make_course(course_id=1)
    lecturer = _make_lecturer(user_id=42, email="jan.novak@tul.cz")

    current_user = MagicMock(spec=User)
    current_user.id = 5
    current_user.role = UserRole.STUDENT

    session = MagicMock()
    with (
        patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [lecturer]},
        ),
        patch("services.courses.get_course_evaluations", new_callable=AsyncMock, return_value=[]),
    ):
        result = await CoursesService(session).get_course(1, current_user=current_user)

    assert result is not None
    assert len(result.lecturers) == 1
    assert result.lecturers[0].email == "jan.novak@tul.cz"


async def test_unauthenticated_caller_receives_null_lecturer_email() -> None:
    """Unauthenticated callers must receive ``null`` for lecturer e-mail addresses."""
    course = _make_course(course_id=1)
    lecturer = _make_lecturer(user_id=42, email="jan.novak@tul.cz")

    session = MagicMock()
    with (
        patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [lecturer]},
        ),
    ):
        result = await CoursesService(session).get_course(1, current_user=None)

    assert result is not None
    assert len(result.lecturers) == 1
    assert result.lecturers[0].email is None


async def test_get_course_returns_none_when_not_found() -> None:
    """``get_course`` must return ``None`` when the DB has no matching row."""
    session = MagicMock()
    with patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=None):
        result = await CoursesService(session).get_course(99, current_user=None)

    assert result is None


async def test_admin_receives_course_evaluations() -> None:
    """An admin caller must always receive ``course_evaluations``."""
    course = _make_course(course_id=1)
    evaluation = _make_evaluation()

    current_user = MagicMock(spec=User)
    current_user.id = 1
    current_user.role = UserRole.ADMIN

    session = MagicMock()
    with (
        patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
            return_value=[evaluation],
        ),
    ):
        result = await CoursesService(session).get_course(1, current_user=current_user)

    assert result is not None
    assert result.course_evaluations is not None
    assert len(result.course_evaluations) == 1


# ---------------------------------------------------------------------------
# CoursesService.create_course — permission and delegation
# ---------------------------------------------------------------------------


async def test_create_course_raises_permission_error_for_non_admin() -> None:
    """``create_course`` must raise ``CoursePermissionError`` for non-admin users."""
    from services.courses import CoursePermissionError

    session = MagicMock()
    current_user = MagicMock(spec=User)
    current_user.id = 5
    current_user.role = UserRole.LECTURER

    with pytest.raises(CoursePermissionError):
        await CoursesService(session).create_course(
            MagicMock(),
            current_user,
        )


async def test_create_course_calls_db_create_and_commits() -> None:
    """``create_course`` must call the DB create function and commit the session."""
    from schemas.courses import CourseCreate

    session = MagicMock()
    session.commit = AsyncMock()

    current_user = MagicMock(spec=User)
    current_user.id = 1
    current_user.role = UserRole.ADMIN

    created_course = _make_course(course_id=10)
    data = CourseCreate(
        code="TEST",
        name="Test Course",
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=50,
    )

    with (
        patch(
            "services.courses.db_create_course",
            new_callable=AsyncMock,
            return_value=created_course,
        ),
        patch(
            "services.courses.db_get_course",
            new_callable=AsyncMock,
            return_value=created_course,
        ),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: []},
        ),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await CoursesService(session).create_course(data, current_user)

    session.commit.assert_called_once()
    assert result is not None
    assert result.id == 10


# ---------------------------------------------------------------------------
# CoursesService.update_course — permission and delegation
# ---------------------------------------------------------------------------


async def test_update_course_returns_none_when_course_not_found() -> None:
    """``update_course`` must return ``None`` when no course with the given id exists."""
    from schemas.courses import CourseUpdate

    session = MagicMock()

    current_user = MagicMock(spec=User)
    current_user.id = 1
    current_user.role = UserRole.ADMIN

    with patch("services.courses.db_get_course", new_callable=AsyncMock, return_value=None):
        result = await CoursesService(session).update_course(999, CourseUpdate(), current_user)

    assert result is None


async def test_update_course_raises_permission_error_for_student() -> None:
    """``update_course`` must raise ``CoursePermissionError`` for students."""
    from schemas.courses import CourseUpdate
    from services.courses import CoursePermissionError

    session = MagicMock()
    course = _make_course(course_id=1)

    current_user = MagicMock(spec=User)
    current_user.id = 5
    current_user.role = UserRole.STUDENT

    with (
        patch(
            "services.courses.db_get_course",
            new_callable=AsyncMock,
            return_value=course,
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        pytest.raises(CoursePermissionError),
    ):
        await CoursesService(session).update_course(1, CourseUpdate(), current_user)


async def test_update_course_raises_permission_error_for_non_assigned_lecturer() -> None:
    """``update_course`` must raise ``CoursePermissionError`` for unassigned lecturers."""
    from schemas.courses import CourseUpdate
    from services.courses import CoursePermissionError

    session = MagicMock()
    course = _make_course(course_id=1)
    # The course is assigned to lecturer 42, not to the calling user.
    assigned_lecturer = _make_lecturer(user_id=42)

    current_user = MagicMock(spec=User)
    current_user.id = 99  # Different id.
    current_user.role = UserRole.LECTURER

    with (
        patch(
            "services.courses.db_get_course",
            new_callable=AsyncMock,
            return_value=course,
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [assigned_lecturer]},
        ),
        pytest.raises(CoursePermissionError),
    ):
        await CoursesService(session).update_course(1, CourseUpdate(), current_user)


async def test_update_course_succeeds_for_assigned_lecturer() -> None:
    """``update_course`` must succeed for a lecturer who is assigned to the course."""
    from schemas.courses import CourseUpdate

    session = MagicMock()
    session.commit = AsyncMock()
    course = _make_course(course_id=1)
    assigned_lecturer = _make_lecturer(user_id=42)

    current_user = MagicMock(spec=User)
    current_user.id = 42
    current_user.role = UserRole.LECTURER

    with (
        patch(
            "services.courses.db_get_course",
            new_callable=AsyncMock,
            return_value=course,
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [assigned_lecturer]},
        ),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: [assigned_lecturer]},
        ),
        patch("services.courses.db_update_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await CoursesService(session).update_course(
            1, CourseUpdate(name="Updated"), current_user
        )

    session.commit.assert_called_once()
    assert result is not None


async def test_update_course_succeeds_for_admin() -> None:
    """``update_course`` must succeed for an admin even without a lecturer assignment."""
    from schemas.courses import CourseUpdate

    session = MagicMock()
    session.commit = AsyncMock()
    course = _make_course(course_id=1)

    current_user = MagicMock(spec=User)
    current_user.id = 1
    current_user.role = UserRole.ADMIN

    with (
        patch(
            "services.courses.db_get_course",
            new_callable=AsyncMock,
            return_value=course,
        ),
        patch(
            "services.courses.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        patch("services.courses.db_update_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.courses.get_course_evaluations",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await CoursesService(session).update_course(
            1, CourseUpdate(name="Admin Update"), current_user
        )

    session.commit.assert_called_once()
    assert result is not None
