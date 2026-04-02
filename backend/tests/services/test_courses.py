from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

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
