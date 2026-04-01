from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.course import CourseTerm
from models.user import UserRole
from services.projects import ProjectsService

# ---------------------------------------------------------------------------
# ProjectsService.get_projects unit tests
# ---------------------------------------------------------------------------


async def test_service_returns_empty_list_when_no_rows() -> None:
    """``ProjectsService.get_projects`` must return an empty list when the DB has no rows."""
    session = MagicMock()
    with (
        patch(
            "services.projects.get_projects", new_callable=AsyncMock, return_value=[]
        ) as mock_get_projects,
        patch(
            "services.projects.get_project_members", new_callable=AsyncMock, return_value={}
        ) as mock_get_members,
        patch(
            "services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}
        ) as mock_get_lecturers,
    ):
        result = await ProjectsService(session).get_projects()

    assert result == []
    mock_get_projects.assert_called_once()
    mock_get_members.assert_called_once_with(session, [])
    mock_get_lecturers.assert_called_once_with(session, [])


async def test_service_assembles_project_with_members_and_lecturers() -> None:
    """``ProjectsService.get_projects`` must correctly assemble nested members and lecturers."""
    from models.course import Course
    from models.course import ProjectType as PT
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "Projektový seminář informatiky"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = PT.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "My Project"
    project.description = None
    project.github_url = None
    project.live_url = None
    project.technologies = []
    project.academic_year = 2025
    project.course_id = 10

    member = MagicMock(spec=User)
    member.id = 5
    member.name = "Alice"
    member.github_alias = "alice"

    lecturer = MagicMock(spec=User)
    lecturer.name = "Prof. Smith"
    lecturer.github_alias = "psmith"

    session = MagicMock()
    with (
        patch(
            "services.projects.get_projects",
            new_callable=AsyncMock,
            return_value=[(project, course)],
        ),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [member]},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [lecturer]},
        ),
    ):
        results = await ProjectsService(session).get_projects()

    assert len(results) == 1
    result = results[0]
    assert result.title == "My Project"
    assert result.members[0].name == "Alice"
    assert result.course.lecturers[0].name == "Prof. Smith"


# ---------------------------------------------------------------------------
# ProjectsService.get_project unit tests
# ---------------------------------------------------------------------------


async def test_service_get_project_returns_none_when_not_found() -> None:
    """``ProjectsService.get_project`` must return ``None`` when the DB row is absent."""
    session = MagicMock()
    with patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None):
        result = await ProjectsService(session).get_project(99)
    assert result is None


async def test_service_get_project_assembles_full_response() -> None:
    """``ProjectsService.get_project`` must assemble a full ``ProjectPublic`` from DB rows."""
    from models.course import Course
    from models.course import ProjectType as PT
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "Projektový seminář informatiky"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = PT.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "My Project"
    project.description = None
    project.github_url = None
    project.live_url = None
    project.technologies = []
    project.academic_year = 2025

    member = MagicMock(spec=User)
    member.id = 5
    member.name = "Alice"
    member.github_alias = "alice"

    lecturer = MagicMock(spec=User)
    lecturer.name = "Prof. Smith"
    lecturer.github_alias = "psmith"

    session = MagicMock()
    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [member]},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [lecturer]},
        ),
    ):
        result = await ProjectsService(session).get_project(1)

    assert result is not None
    assert result.title == "My Project"
    assert result.members[0].name == "Alice"
    assert result.course.lecturers[0].name == "Prof. Smith"


async def test_service_get_project_raises_when_project_id_is_none() -> None:
    """``ProjectsService.get_project`` must raise ``ValueError`` for a project row with no id."""
    from models.course import Course
    from models.course import ProjectType as PT
    from models.project import Project

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "Projektový seminář informatiky"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = PT.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = None  # Simulate a corrupt/unsaved row.

    session = MagicMock()
    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}),
        pytest.raises(ValueError, match="no id"),
    ):
        await ProjectsService(session).get_project(1)


# ---------------------------------------------------------------------------
# ProjectsService.get_project_detail unit tests
# ---------------------------------------------------------------------------


def _make_project_and_course() -> tuple:
    """Return shared mock project and course objects for service unit tests."""
    from models.course import Course
    from models.course import ProjectType as PT
    from models.project import Project

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "Projektový seminář informatiky"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = PT.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "My Project"
    project.description = None
    project.github_url = None
    project.live_url = None
    project.technologies = []
    project.academic_year = 2025
    project.results_unlocked = False

    return project, course


async def test_service_get_project_detail_returns_none_when_not_found() -> None:
    """``get_project_detail`` must return ``None`` when the project row is absent."""
    from models.user import User

    session = MagicMock()
    user = MagicMock(spec=User)
    user.role = UserRole.STUDENT
    user.id = 1

    with patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None):
        result = await ProjectsService(session).get_project_detail(99, user)
    assert result is None


async def test_service_get_project_detail_includes_emails() -> None:
    """``get_project_detail`` must include e-mails for members and lecturers."""
    from models.user import User

    project, course = _make_project_and_course()

    member = MagicMock(spec=User)
    member.id = 5
    member.name = "Alice"
    member.github_alias = "alice"
    member.email = "alice@tul.cz"

    lecturer = MagicMock(spec=User)
    lecturer.name = "Prof. Smith"
    lecturer.github_alias = "psmith"
    lecturer.email = "smith@tul.cz"

    user = MagicMock(spec=User)
    user.role = UserRole.STUDENT
    user.id = 5

    session = MagicMock()
    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [member]},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [lecturer]},
        ),
    ):
        result = await ProjectsService(session).get_project_detail(1, user)

    assert result is not None
    assert result.members[0].email == "alice@tul.cz"
    assert result.course.lecturers[0].email == "smith@tul.cz"
    assert result.results_unlocked is False


async def test_service_get_project_detail_no_evaluations_when_not_unlocked() -> None:
    """``get_project_detail`` must not attach evaluations when ``results_unlocked=False``."""
    from models.user import User

    project, course = _make_project_and_course()
    project.results_unlocked = False

    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 10

    session = MagicMock()
    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        result = await ProjectsService(session).get_project_detail(1, user)

    assert result is not None
    assert result.project_evaluations is None
    assert result.course_evaluations is None


async def test_service_get_project_detail_lecturer_sees_all_evaluations() -> None:
    """Lecturer/admin ``get_project_detail`` with results_unlocked must attach all evaluations."""
    from datetime import UTC, datetime

    from models.course_evaluation import CourseEvaluation
    from models.project_evaluation import ProjectEvaluation
    from models.user import User

    project, course = _make_project_and_course()
    project.results_unlocked = True

    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 10

    proj_eval = MagicMock(spec=ProjectEvaluation)
    proj_eval.lecturer_id = 10
    proj_eval.scores = []
    proj_eval.submitted_at = datetime(2025, 1, 1, tzinfo=UTC)

    course_eval = MagicMock(spec=CourseEvaluation)
    course_eval.id = 1
    course_eval.student_id = 5
    course_eval.rating = 4
    course_eval.strengths = "Good"
    course_eval.improvements = "Better"
    course_eval.published = True
    course_eval.submitted_at = datetime(2025, 1, 2, tzinfo=UTC)

    session = MagicMock()
    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}),
        patch(
            "services.projects.get_project_evaluations",
            new_callable=AsyncMock,
            return_value=[proj_eval],
        ),
        patch(
            "services.projects.get_course_evaluations",
            new_callable=AsyncMock,
            return_value=[course_eval],
        ),
    ):
        result = await ProjectsService(session).get_project_detail(1, user)

    assert result is not None
    assert result.project_evaluations is not None
    assert len(result.project_evaluations) == 1
    assert result.course_evaluations is not None
    assert len(result.course_evaluations) == 1
    assert result.received_peer_feedback is None
    assert result.authored_peer_feedback is None


async def test_service_get_project_detail_student_sees_peer_feedback_not_course_evals() -> None:
    """Student ``get_project_detail`` with unlocked results must attach peer feedback only.

    Course evaluations must be ``None`` — students cannot see other students' evaluations.
    """
    from datetime import UTC, datetime

    from models.peer_feedback import PeerFeedback
    from models.project_evaluation import ProjectEvaluation
    from models.user import User

    project, course = _make_project_and_course()
    project.results_unlocked = True

    user = MagicMock(spec=User)
    user.role = UserRole.STUDENT
    user.id = 5

    proj_eval = MagicMock(spec=ProjectEvaluation)
    proj_eval.lecturer_id = 10
    proj_eval.scores = []
    proj_eval.submitted_at = datetime(2025, 1, 1, tzinfo=UTC)

    received_fb = MagicMock(spec=PeerFeedback)
    received_fb.course_evaluation_id = 1
    received_fb.receiving_student_id = 5
    received_fb.strengths = "Great teamwork"
    received_fb.improvements = "More commits"
    received_fb.bonus_points = 3

    authored_fb = MagicMock(spec=PeerFeedback)
    authored_fb.course_evaluation_id = 1
    authored_fb.receiving_student_id = 6
    authored_fb.strengths = "Helped a lot"
    authored_fb.improvements = "Be on time"
    authored_fb.bonus_points = 2

    session = MagicMock()
    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}),
        patch(
            "services.projects.get_project_evaluations",
            new_callable=AsyncMock,
            return_value=[proj_eval],
        ),
        patch(
            "services.projects.get_peer_feedback_received",
            new_callable=AsyncMock,
            return_value=[received_fb],
        ),
        patch(
            "services.projects.get_peer_feedback_authored",
            new_callable=AsyncMock,
            return_value=[authored_fb],
        ),
    ):
        result = await ProjectsService(session).get_project_detail(1, user)

    assert result is not None
    assert result.project_evaluations is not None
    assert len(result.project_evaluations) == 1
    assert result.course_evaluations is None  # Students do not see course evaluations.
    assert result.received_peer_feedback is not None
    assert result.received_peer_feedback[0].receiving_student_id == 5
    assert result.authored_peer_feedback is not None
    assert result.authored_peer_feedback[0].receiving_student_id == 6
