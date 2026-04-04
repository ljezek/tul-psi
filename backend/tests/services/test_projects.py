from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.course import CourseTerm
from models.user import UserRole
from services.projects import (
    AlreadyMemberError,
    InvalidEvaluationDataError,
    PermissionDeniedError,
    ProjectNotFoundError,
    ProjectsService,
)

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
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        results = await ProjectsService(session).get_projects()

    assert len(results) == 1
    result = results[0]
    assert result.title == "My Project"
    assert result.members[0].name == "Alice"
    assert result.course.lecturers[0].name == "Prof. Smith"


async def test_service_get_projects_optimizes_evaluation_fetching_for_members() -> None:
    """``get_projects`` must only fetch course evaluations for projects where the user is a member."""
    from models.course import Course, ProjectType
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "Projektový seminář informatiky"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = ProjectType.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    # Two projects: user is a member of project 1, but not project 2.
    p1 = MagicMock(spec=Project)
    p1.id = 1
    p1.course_id = 10
    p1.title = "Project 1"
    p1.description = None
    p1.github_url = None
    p1.live_url = None
    p1.technologies = []
    p1.academic_year = 2025

    p2 = MagicMock(spec=Project)
    p2.id = 2
    p2.course_id = 10
    p2.title = "Project 2"
    p2.description = None
    p2.github_url = None
    p2.live_url = None
    p2.technologies = []
    p2.academic_year = 2025

    user = MagicMock(spec=User)
    user.id = 5

    member = MagicMock(spec=User)
    member.id = 5
    member.name = "Alice"
    member.github_alias = "alice"
    member.email = "alice@tul.cz"

    session = MagicMock()
    with (
        patch(
            "services.projects.get_projects",
            new_callable=AsyncMock,
            return_value=[(p1, course), (p2, course)],
        ),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            # User is only member of project 1
            return_value={1: [member], 2: []},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: []},
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluations_for_student",
            new_callable=AsyncMock,
            return_value={},
        ) as mock_get_evals,
        patch("services.projects.get_project_evaluations", new_callable=AsyncMock, return_value=[]),
        patch("services.projects.get_peer_feedback_received", new_callable=AsyncMock, return_value=[]),
    ):
        await ProjectsService(session).get_projects(user=user)

    # Optimization check: get_course_evaluations_for_student should be called with [1], not [1, 2].
    mock_get_evals.assert_called_once_with(session, [1], 5)


async def test_service_get_projects_calculates_total_points_when_unlocked() -> None:
    """``get_projects`` must calculate ``total_points`` (lecturer avg + peer avg) for member projects."""
    from datetime import datetime
    from models.course import Course, CourseTerm, ProjectType
    from models.project import Project
    from models.user import User
    from schemas.projects import ProjectEvaluationDetail, EvaluationScoreDetail, PeerFeedbackDetail

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "Test Course"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = ProjectType.TEAM
    course.min_score = 50
    course.peer_bonus_budget = 10
    course.evaluation_criteria = []
    course.links = []

    p = MagicMock(spec=Project)
    p.id = 1
    p.course_id = 10
    p.title = "My Project"
    p.description = None
    p.github_url = None
    p.live_url = None
    p.technologies = []
    p.academic_year = 2025
    p.results_unlocked = True

    user = MagicMock(spec=User)
    user.id = 5
    user.name = "Alice"

    member = MagicMock(spec=User)
    member.id = 5
    member.name = "Alice"
    member.github_alias = "alice"
    member.email = "alice@tul.cz"

    # Lecturer evaluations: 
    # Lect 1: 40 points total across criteria
    # Lect 2: 50 points total across criteria
    # Avg Lecturer = 45.0
    peval1 = ProjectEvaluationDetail(
        lecturer_id=1,
        submitted=True,
        updated_at=datetime.now(),
        scores=[EvaluationScoreDetail(criterion_code="C1", score=40, strengths="", improvements="")]
    )
    peval2 = ProjectEvaluationDetail(
        lecturer_id=2,
        submitted=True,
        updated_at=datetime.now(),
        scores=[EvaluationScoreDetail(criterion_code="C1", score=50, strengths="", improvements="")]
    )

    # Peer feedback: 
    # Peer A: +5 points
    # Peer B: +15 points
    # Avg Peer = 10.0
    pfeed1 = PeerFeedbackDetail(course_evaluation_id=1, receiving_student_id=5, bonus_points=5, strengths=None, improvements=None)
    pfeed2 = PeerFeedbackDetail(course_evaluation_id=2, receiving_student_id=5, bonus_points=15, strengths=None, improvements=None)

    session = MagicMock()
    with (
        patch("services.projects.get_projects", new_callable=AsyncMock, return_value=[(p, course)]),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={1: [member]}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={10: []}),
        patch("services.projects.get_evaluation_counts_for_projects", new_callable=AsyncMock, return_value={1: (2, 2)}),
        patch("services.projects.get_course_evaluations_for_student", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_project_evaluations", new_callable=AsyncMock, return_value=[]), # Not used since we patch the mapping loop below
        patch("services.projects._to_project_evaluation_detail", side_effect=[peval1, peval2]),
        patch("services.projects.get_project_evaluations", new_callable=AsyncMock, return_value=["raw1", "raw2"]),
        patch("services.projects.get_peer_feedback_received", new_callable=AsyncMock, return_value=["fraw1", "fraw2"]),
        patch("services.projects._to_peer_feedback_detail", side_effect=[pfeed1, pfeed2]),
    ):
        results = await ProjectsService(session).get_projects(user=user)

    assert len(results) == 1
    # Total = 45.0 (lecturer avg) + 10.0 (peer avg) = 55.0
    assert results[0].total_points == 55.0


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
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
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
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        pytest.raises(ValueError, match="no id"),
    ):
        await ProjectsService(session).get_project(1)


# ---------------------------------------------------------------------------
# ProjectsService.get_project_detail unit tests
# ---------------------------------------------------------------------------


def _make_project_and_course() -> tuple[MagicMock, MagicMock]:
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


def _make_seeding_project_and_course() -> tuple[MagicMock, MagicMock]:
    """Return minimal mock project and course objects for seeding/management tests.

    Uses ``id=1`` for the course and ``id=5`` for the project, distinct from
    the values used by ``_make_project_and_course`` to avoid cross-test interference.
    """
    from models.course import Course
    from models.project import Project

    course = MagicMock(spec=Course)
    course.id = 1

    project = MagicMock(spec=Project)
    project.id = 5

    return project, course


def _make_admin_user() -> MagicMock:
    """Return a mock ADMIN user with id=1."""
    from models.user import User

    user = MagicMock(spec=User)
    user.id = 1
    user.role = UserRole.ADMIN
    return user


def _make_lecturer_user(user_id: int = 7) -> MagicMock:
    """Return a mock LECTURER user with the specified id."""
    from models.user import User

    user = MagicMock(spec=User)
    user.id = user_id
    user.role = UserRole.LECTURER
    return user


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
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
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
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
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
    proj_eval.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

    course_eval = MagicMock(spec=CourseEvaluation)
    course_eval.id = 1
    course_eval.student_id = 5
    course_eval.rating = 4
    course_eval.strengths = "Good"
    course_eval.improvements = "Better"
    course_eval.submitted = True
    course_eval.updated_at = datetime(2025, 1, 2, tzinfo=UTC)

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
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
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
    proj_eval.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

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
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
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


# ---------------------------------------------------------------------------
# ProjectsService.create_project unit tests
# ---------------------------------------------------------------------------


async def test_service_create_project_raises_lookup_error_when_course_not_found() -> None:
    """``create_project`` must raise ``LookupError`` when the course does not exist."""
    from schemas.projects import ProjectCreate

    session = MagicMock()
    user = _make_admin_user()
    data = ProjectCreate(title="Test", academic_year=2025)

    with (
        patch("services.projects.db_get_course", new_callable=AsyncMock, return_value=None),
        pytest.raises(LookupError),
    ):
        await ProjectsService(session).create_project(99, data, user)


async def test_service_create_project_raises_permission_error_for_unassigned_lecturer() -> None:
    """``create_project`` must raise ``PermissionError`` when lecturer is not assigned."""
    from schemas.projects import ProjectCreate

    _project, course = _make_seeding_project_and_course()
    session = MagicMock()
    user = _make_lecturer_user(user_id=5)
    data = ProjectCreate(title="Test", academic_year=2025)

    with (
        patch("services.projects.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        pytest.raises(PermissionError),
    ):
        await ProjectsService(session).create_project(1, data, user)


async def test_service_create_project_succeeds_for_admin() -> None:
    """``create_project`` must create a project when called by an admin."""
    from schemas.projects import ProjectCreate

    project, course = _make_project_and_course()
    project.id = 10
    project.title = "Test"
    session = MagicMock()
    user = _make_admin_user()
    data = ProjectCreate(title="Test", academic_year=2025)

    with (
        patch("services.projects.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.projects.db_create_project",
            new_callable=AsyncMock,
            return_value=project,
        ),
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch.object(session, "commit", new_callable=AsyncMock),
        patch.object(session, "refresh", new_callable=AsyncMock),
    ):
        result = await ProjectsService(session).create_project(1, data, user)

    assert result is not None
    assert result.id == 10


# ---------------------------------------------------------------------------
# ProjectsService.delete_project unit tests
# ---------------------------------------------------------------------------


async def test_service_delete_project_raises_lookup_error_when_not_found() -> None:
    """``delete_project`` must raise ``LookupError`` when the project does not exist."""
    session = MagicMock()
    user = _make_admin_user()

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(LookupError),
    ):
        await ProjectsService(session).delete_project(99, user)


async def test_service_delete_project_raises_permission_error_for_unassigned_lecturer() -> None:
    """``delete_project`` must raise ``PermissionError`` when lecturer is not assigned."""
    project, course = _make_seeding_project_and_course()
    session = MagicMock()
    user = _make_lecturer_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        pytest.raises(PermissionError),
    ):
        await ProjectsService(session).delete_project(5, user)


async def test_service_delete_project_succeeds_for_admin() -> None:
    """``delete_project`` must delete the project when called by an admin."""
    project, course = _make_seeding_project_and_course()
    session = MagicMock()
    user = _make_admin_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.db_delete_project", new_callable=AsyncMock, return_value=True),
        patch.object(session, "commit", new_callable=AsyncMock),
    ):
        await ProjectsService(session).delete_project(5, user)


# ---------------------------------------------------------------------------
# ProjectsService.unlock_project unit tests
# ---------------------------------------------------------------------------


async def test_service_unlock_project_raises_lookup_error_when_not_found() -> None:
    """``unlock_project`` must raise ``LookupError`` when the project does not exist."""
    session = MagicMock()
    user = _make_admin_user()

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(LookupError),
    ):
        await ProjectsService(session).unlock_project(99, user)


async def test_service_unlock_project_raises_permission_error_for_unassigned_lecturer() -> None:
    """``unlock_project`` must raise ``PermissionError`` when lecturer is not assigned."""
    project, course = _make_seeding_project_and_course()
    session = MagicMock()
    user = _make_lecturer_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        pytest.raises(PermissionError),
    ):
        await ProjectsService(session).unlock_project(5, user)


async def test_service_unlock_project_sets_results_unlocked() -> None:
    """``unlock_project`` must set ``results_unlocked=True`` and return the project."""
    project, course = _make_project_and_course()
    project.id = 5
    project.results_unlocked = True  # Value returned after the unlock.
    session = MagicMock()
    user = _make_admin_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.db_unlock_project_results",
            new_callable=AsyncMock,
            return_value=project,
        ),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch("services.projects.get_project_evaluations", new_callable=AsyncMock, return_value=[]),
        patch("services.projects.get_course_evaluations", new_callable=AsyncMock, return_value=[]),
        patch.object(session, "commit", new_callable=AsyncMock),
    ):
        result = await ProjectsService(session).unlock_project(5, user)

    assert result is not None
    assert result.id == 5
    assert result.results_unlocked is True


# ---------------------------------------------------------------------------
# ProjectsService.patch_project unit tests
# ---------------------------------------------------------------------------


async def test_patch_project_raises_not_found_when_project_missing() -> None:
    """``patch_project`` must raise ``ProjectNotFoundError`` when the project does not exist."""
    from models.user import User

    session = MagicMock()
    user = MagicMock(spec=User)
    user.id = 1
    user.role = UserRole.STUDENT

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(ProjectNotFoundError),
    ):
        from schemas.projects import ProjectUpdate

        await ProjectsService(session).patch_project(
            99,
            ProjectUpdate(title="X"),
            user,
        )


async def test_patch_project_raises_permission_denied_when_not_member() -> None:
    """``patch_project`` must raise ``PermissionDeniedError`` when caller is not a member."""
    from models.course import Course
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    project = MagicMock(spec=Project)
    project.id = 1

    session = MagicMock()
    user = MagicMock(spec=User)
    user.id = 99
    user.role = UserRole.STUDENT

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "services.projects.is_project_member",
            new_callable=AsyncMock,
            return_value=False,
        ),
        pytest.raises(PermissionDeniedError),
    ):
        from schemas.projects import ProjectUpdate

        await ProjectsService(session).patch_project(1, ProjectUpdate(title="X"), user)


async def test_patch_project_member_can_update() -> None:
    """``patch_project`` must write updates and return the enriched project for a member."""
    from models.course import Course, ProjectType
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "PSI"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = ProjectType.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "Updated"
    project.description = None
    project.github_url = None
    project.live_url = None
    project.technologies = []
    project.academic_year = 2025
    project.results_unlocked = False

    session = MagicMock()
    session.commit = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 5
    user.role = UserRole.STUDENT

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "services.projects.is_project_member",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch("services.projects.update_project", new_callable=AsyncMock, return_value=project),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: []},
        ),
        patch("services.projects.get_evaluation_counts_for_projects", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_evaluation_by_student", new_callable=AsyncMock, return_value=None),    ):
        from schemas.projects import ProjectUpdate

        result = await ProjectsService(session).patch_project(
            1, ProjectUpdate(title="Updated"), user
        )

    assert result is not None
    assert result.title == "Updated"
    session.commit.assert_called_once()


async def test_patch_project_lecturer_can_update_without_membership() -> None:
    """``patch_project`` must allow a lecturer to update even without project membership."""
    from models.course import Course, ProjectType
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "PSI"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = ProjectType.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "Lecturer Update"
    project.description = None
    project.github_url = None
    project.live_url = None
    project.technologies = []
    project.academic_year = 2025
    project.results_unlocked = False

    session = MagicMock()
    session.commit = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 7
    user.role = UserRole.LECTURER

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch("services.projects.update_project", new_callable=AsyncMock, return_value=project),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: []},
        ),
        patch("services.projects.get_evaluation_counts_for_projects", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_evaluation_by_student", new_callable=AsyncMock, return_value=None),    ):
        from schemas.projects import ProjectUpdate

        result = await ProjectsService(session).patch_project(
            1, ProjectUpdate(title="Lecturer Update"), user
        )

    assert result is not None
    assert result.title == "Lecturer Update"


async def test_patch_project_grants_admin_write_access() -> None:
    """``patch_project`` must grant write access to ADMIN users unconditionally.

    An ADMIN who is neither a project member nor a course lecturer must still
    be able to update the project — admins have blanket superuser access.
    """
    from models.course import Course, ProjectType
    from models.project import Project
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    course.code = "PSI"
    course.name = "PSI"
    course.syllabus = None
    course.term = CourseTerm.WINTER
    course.project_type = ProjectType.TEAM
    course.min_score = 50
    course.peer_bonus_budget = None
    course.evaluation_criteria = []
    course.links = []

    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "Admin Update"
    project.description = None
    project.github_url = None
    project.live_url = None
    project.technologies = []
    project.academic_year = 2025
    project.results_unlocked = False

    session = MagicMock()
    session.commit = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 3
    user.role = UserRole.ADMIN

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        # is_course_lecturer must NOT be called for admins — they have unconditional access.
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_is_lecturer,
        patch("services.projects.update_project", new_callable=AsyncMock, return_value=project),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        patch(
            "services.projects.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: []},
        ),
        patch("services.projects.get_evaluation_counts_for_projects", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_evaluation_by_student", new_callable=AsyncMock, return_value=None),    ):
        from schemas.projects import ProjectUpdate

        result = await ProjectsService(session).patch_project(
            1, ProjectUpdate(title="Admin Update"), user
        )

    assert result is not None
    assert result.title == "Admin Update"
    mock_is_lecturer.assert_not_called()


# ---------------------------------------------------------------------------
# ProjectsService.add_member unit tests
# ---------------------------------------------------------------------------


async def test_add_member_raises_not_found_when_project_missing() -> None:
    """``add_member`` must raise ``ProjectNotFoundError`` when the project does not exist."""
    from models.user import User

    session = MagicMock()
    user = MagicMock(spec=User)
    user.id = 1
    user.role = UserRole.STUDENT

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(ProjectNotFoundError),
    ):
        from schemas.projects import AddMemberBody

        await ProjectsService(session).add_member(99, AddMemberBody(email="x@tul.cz"), user)


async def test_add_member_raises_already_member_when_duplicate() -> None:
    """``add_member`` must raise ``AlreadyMemberError`` when the user is already a member."""
    from models.course import Course
    from models.project import Project
    from models.project_member import ProjectMember
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    project = MagicMock(spec=Project)
    project.id = 1

    existing_user = MagicMock(spec=User)
    existing_user.id = 10
    existing_user.email = "bob@tul.cz"
    existing_user.name = "Bob"
    existing_user.github_alias = None

    existing_member = MagicMock(spec=ProjectMember)

    session = MagicMock()
    user = MagicMock(spec=User)
    user.id = 5
    user.role = UserRole.STUDENT

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "services.projects.is_project_member",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "services.projects.get_or_create_user",
            new_callable=AsyncMock,
            return_value=(existing_user, False),
        ),
        patch(
            "services.projects.add_project_member",
            new_callable=AsyncMock,
            return_value=(existing_member, False),
        ),
        pytest.raises(AlreadyMemberError),
    ):
        from schemas.projects import AddMemberBody

        await ProjectsService(session).add_member(1, AddMemberBody(email="bob@tul.cz"), user)


async def test_add_member_creates_user_and_returns_member_public() -> None:
    """``add_member`` must create a new user when none exists and return ``MemberPublic``."""
    from models.course import Course
    from models.project import Project
    from models.project_member import ProjectMember
    from models.user import User

    course = MagicMock(spec=Course)
    course.id = 10
    project = MagicMock(spec=Project)
    project.id = 1

    new_user = MagicMock(spec=User)
    new_user.id = 20
    new_user.email = "new@tul.cz"
    new_user.name = "new@tul.cz"
    new_user.github_alias = None

    new_member = MagicMock(spec=ProjectMember)
    new_member.id = 100

    session = MagicMock()
    session.commit = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 5
    user.role = UserRole.STUDENT

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "services.projects.is_project_member",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "services.projects.get_or_create_user",
            new_callable=AsyncMock,
            return_value=(new_user, True),
        ),
        patch(
            "services.projects.add_project_member",
            new_callable=AsyncMock,
            return_value=(new_member, True),
        ),
        patch(
            "services.projects.get_settings",
            return_value=MagicMock(frontend_url="http://localhost:5173", app_env="local"),
        ),
        patch("services.projects.EmailSender"),  # Prevent real email side-effects.
    ):
        from schemas.projects import AddMemberBody

        result = await ProjectsService(session).add_member(
            1, AddMemberBody(email="new@tul.cz"), user
        )

    assert result.id == 20
    assert result.email == "new@tul.cz"
    session.commit.assert_called_once()


async def test_service_create_project_with_owner_sends_invite_email() -> None:
    """``create_project`` must send a project invite to the owner when ``owner_email`` is set."""
    from models.project_member import ProjectMember
    from models.user import User
    from schemas.projects import ProjectCreate

    project, course = _make_project_and_course()
    project.id = 10
    project.title = "Test"
    course.name = "PSI"
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    user = _make_admin_user()
    data = ProjectCreate(title="Test", academic_year=2025, owner_email="owner@tul.cz")

    owner_user = MagicMock(spec=User)
    owner_user.id = 42
    owner_user.email = "owner@tul.cz"
    new_member = MagicMock(spec=ProjectMember)

    mock_sender_instance = MagicMock()

    with (
        patch("services.projects.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.projects.db_create_project",
            new_callable=AsyncMock,
            return_value=project,
        ),
        patch(
            "services.projects.get_or_create_user",
            new_callable=AsyncMock,
            return_value=(owner_user, True),
        ),
        patch(
            "services.projects.add_project_member",
            new_callable=AsyncMock,
            return_value=(new_member, True),
        ),
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.get_project_members", new_callable=AsyncMock, return_value={}),
        patch("services.projects.get_course_lecturers", new_callable=AsyncMock, return_value={}),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.projects.get_evaluation_counts_for_projects",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "services.projects.get_settings",
            return_value=MagicMock(frontend_url="http://localhost:5173", app_env="local"),
        ),
        patch("services.projects.EmailSender", return_value=mock_sender_instance),
    ):
        result = await ProjectsService(session).create_project(1, data, user)

    assert result is not None
    assert result.id == 10
    mock_sender_instance.send.assert_called_once()
    session.commit.assert_called_once()


async def test_service_create_project_with_owner_raises_email_delivery_error() -> None:
    """``create_project`` must raise ``EmailDeliveryNotImplementedError`` on send failure.

    The project and member row must be committed before the error is raised.
    """
    from models.project_member import ProjectMember
    from models.user import User
    from schemas.projects import ProjectCreate
    from services.email import EmailDeliveryNotImplementedError

    project, course = _make_project_and_course()
    project.id = 10
    project.title = "Test"
    course.name = "PSI"
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    user = _make_admin_user()
    data = ProjectCreate(title="Test", academic_year=2025, owner_email="owner@tul.cz")

    owner_user = MagicMock(spec=User)
    owner_user.id = 42
    owner_user.email = "owner@tul.cz"
    new_member = MagicMock(spec=ProjectMember)

    mock_sender_instance = MagicMock()
    mock_sender_instance.send.side_effect = EmailDeliveryNotImplementedError("No SMTP configured")

    with (
        patch("services.projects.db_get_course", new_callable=AsyncMock, return_value=course),
        patch(
            "services.projects.db_create_project",
            new_callable=AsyncMock,
            return_value=project,
        ),
        patch(
            "services.projects.get_or_create_user",
            new_callable=AsyncMock,
            return_value=(owner_user, True),
        ),
        patch(
            "services.projects.add_project_member",
            new_callable=AsyncMock,
            return_value=(new_member, True),
        ),
        patch(
            "services.projects.get_settings",
            return_value=MagicMock(frontend_url="http://localhost:5173", app_env="production"),
        ),
        patch("services.projects.EmailSender", return_value=mock_sender_instance),
        pytest.raises(EmailDeliveryNotImplementedError),
    ):
        await ProjectsService(session).create_project(1, data, user)

    # Project and member rows must be committed before the error is surfaced.
    session.commit.assert_called_once()


async def test_add_member_raises_email_delivery_error_on_send_failure() -> None:
    """``add_member`` must raise ``EmailDeliveryNotImplementedError`` when the sender fails.

    The DB commit must happen *before* the error is raised — the membership row
    must be durable even when email delivery is not available in the environment.
    """
    from models.course import Course
    from models.project import Project
    from models.project_member import ProjectMember
    from models.user import User
    from services.email import EmailDeliveryNotImplementedError

    course = MagicMock(spec=Course)
    course.id = 10
    course.name = "PSI"
    project = MagicMock(spec=Project)
    project.id = 1
    project.title = "My Project"

    new_user = MagicMock(spec=User)
    new_user.id = 20
    new_user.email = "new@tul.cz"
    new_user.name = "new@tul.cz"
    new_user.github_alias = None

    new_member = MagicMock(spec=ProjectMember)
    new_member.id = 100

    session = MagicMock()
    session.commit = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 5
    user.role = UserRole.STUDENT

    mock_sender_instance = MagicMock()
    mock_sender_instance.send.side_effect = EmailDeliveryNotImplementedError("No SMTP configured")

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.is_course_lecturer",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "services.projects.is_project_member",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "services.projects.get_or_create_user",
            new_callable=AsyncMock,
            return_value=(new_user, True),
        ),
        patch(
            "services.projects.add_project_member",
            new_callable=AsyncMock,
            return_value=(new_member, True),
        ),
        patch(
            "services.projects.get_settings",
            return_value=MagicMock(frontend_url="http://localhost:5173", app_env="production"),
        ),
        patch("services.projects.EmailSender", return_value=mock_sender_instance),
        pytest.raises(EmailDeliveryNotImplementedError),
    ):
        from schemas.projects import AddMemberBody

        await ProjectsService(session).add_member(1, AddMemberBody(email="new@tul.cz"), user)

    # The member row must be committed to the DB before the error is surfaced.
    session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# ProjectsService.get_project_evaluation unit tests
# ---------------------------------------------------------------------------


async def test_service_get_project_evaluation_raises_lookup_when_project_missing() -> None:
    """``get_project_evaluation`` must raise ``LookupError`` when the project does not exist."""
    session = MagicMock()
    user = _make_lecturer_user()

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(LookupError),
    ):
        await ProjectsService(session).get_project_evaluation(99, user)


async def test_service_get_project_evaluation_raises_permission_for_unassigned_lecturer() -> None:
    """``get_project_evaluation`` must raise ``PermissionError`` for an unassigned lecturer."""
    project, course = _make_seeding_project_and_course()
    session = MagicMock()
    user = _make_lecturer_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        pytest.raises(PermissionError),
    ):
        await ProjectsService(session).get_project_evaluation(5, user)


async def test_service_get_project_evaluation_raises_lookup_when_no_evaluation() -> None:
    """``get_project_evaluation`` must raise ``LookupError`` when no evaluation row exists."""
    project, course = _make_project_and_course()
    session = MagicMock()
    user = _make_admin_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_project_evaluation_by_lecturer",
            new_callable=AsyncMock,
            return_value=None,
        ),
        pytest.raises(LookupError),
    ):
        await ProjectsService(session).get_project_evaluation(1, user)


async def test_service_get_project_evaluation_returns_detail() -> None:
    """``get_project_evaluation`` must return the evaluation as ``ProjectEvaluationDetail``."""
    from datetime import UTC, datetime

    from models.project_evaluation import ProjectEvaluation

    project, course = _make_project_and_course()
    session = MagicMock()
    user = _make_admin_user()

    evaluation = MagicMock(spec=ProjectEvaluation)
    evaluation.lecturer_id = 1
    evaluation.scores = []
    evaluation.updated_at = datetime(2025, 1, 1, tzinfo=UTC)
    evaluation.submitted = True

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_project_evaluation_by_lecturer",
            new_callable=AsyncMock,
            return_value=evaluation,
        ),
    ):
        result = await ProjectsService(session).get_project_evaluation(1, user)

    assert result.lecturer_id == 1
    assert result.submitted is True


# ---------------------------------------------------------------------------
# ProjectsService.save_project_evaluation unit tests
# ---------------------------------------------------------------------------


async def test_save_project_evaluation_raises_lookup_when_project_missing() -> None:
    """``save_project_evaluation`` must raise ``LookupError`` when the project is absent."""
    from schemas.projects import ProjectEvaluationCreate

    session = MagicMock()
    user = _make_admin_user()

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(LookupError),
    ):
        await ProjectsService(session).save_project_evaluation(
            99, ProjectEvaluationCreate(scores=[]), user
        )


async def test_save_project_evaluation_raises_permission_for_unassigned_lecturer() -> None:
    """``save_project_evaluation`` must raise ``PermissionError`` for unassigned lecturer."""
    from schemas.projects import ProjectEvaluationCreate

    project, course = _make_seeding_project_and_course()
    session = MagicMock()
    user = _make_lecturer_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        pytest.raises(PermissionError),
    ):
        await ProjectsService(session).save_project_evaluation(
            5, ProjectEvaluationCreate(scores=[]), user
        )


async def test_save_project_evaluation_raises_permission_for_unassigned_admin() -> None:
    """``save_project_evaluation`` must raise ``PermissionError`` for admin not on the course.

    Unlike general course management, project evaluations require the caller to be
    explicitly assigned as a course lecturer — admin users without the assignment
    are also denied.
    """
    from schemas.projects import ProjectEvaluationCreate

    project, course = _make_project_and_course()
    session = MagicMock()
    # Admin user whose id (1) is NOT in the returned lecturer list.
    user = _make_admin_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: []},  # Admin is not assigned as a lecturer.
        ),
        pytest.raises(PermissionError),
    ):
        await ProjectsService(session).save_project_evaluation(
            1, ProjectEvaluationCreate(scores=[]), user
        )


async def test_save_project_evaluation_raises_conflict_when_results_unlocked() -> None:
    """``save_project_evaluation`` raises ``EvaluationConflictError`` when unlocked."""
    from schemas.projects import ProjectEvaluationCreate
    from services.projects import EvaluationConflictError

    project, course = _make_project_and_course()
    project.results_unlocked = True
    session = MagicMock()
    user = _make_lecturer_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [MagicMock(id=user.id)]},
        ),
        pytest.raises(EvaluationConflictError),
    ):
        await ProjectsService(session).save_project_evaluation(
            1, ProjectEvaluationCreate(scores=[]), user
        )


async def test_save_project_evaluation_raises_for_invalid_criterion_code() -> None:
    """``save_project_evaluation`` raises ``InvalidEvaluationDataError`` for unknown codes."""
    from models.course import EvaluationCriterion
    from schemas.projects import EvaluationScoreDetail, ProjectEvaluationCreate

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.evaluation_criteria = [
        EvaluationCriterion(code="code_quality", description="Code Quality", max_score=25)
    ]
    session = MagicMock()
    user = _make_lecturer_user()

    body = ProjectEvaluationCreate(
        scores=[
            EvaluationScoreDetail(
                criterion_code="nonexistent",
                score=10,
                strengths="Good",
                improvements="Bad",
            )
        ]
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [MagicMock(id=user.id)]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="nonexistent"),
    ):
        await ProjectsService(session).save_project_evaluation(1, body, user)


async def test_save_project_evaluation_raises_for_score_exceeding_max() -> None:
    """``save_project_evaluation`` raises ``InvalidEvaluationDataError`` when score > max."""
    from models.course import EvaluationCriterion
    from schemas.projects import EvaluationScoreDetail, ProjectEvaluationCreate

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.evaluation_criteria = [
        EvaluationCriterion(code="code_quality", description="Code Quality", max_score=25)
    ]
    session = MagicMock()
    user = _make_lecturer_user()

    body = ProjectEvaluationCreate(
        scores=[
            EvaluationScoreDetail(
                criterion_code="code_quality",
                score=30,  # Exceeds max_score of 25.
                strengths="Good",
                improvements="Bad",
            )
        ]
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [MagicMock(id=user.id)]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="30"),
    ):
        await ProjectsService(session).save_project_evaluation(1, body, user)


async def test_save_project_evaluation_raises_for_negative_score() -> None:
    """``save_project_evaluation`` raises ``InvalidEvaluationDataError`` when score < 0."""
    from models.course import EvaluationCriterion
    from schemas.projects import EvaluationScoreDetail, ProjectEvaluationCreate

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.evaluation_criteria = [
        EvaluationCriterion(code="code_quality", description="Code Quality", max_score=25)
    ]
    session = MagicMock()
    user = _make_lecturer_user()

    body = ProjectEvaluationCreate(
        scores=[
            EvaluationScoreDetail(
                criterion_code="code_quality",
                score=-1,
                strengths="Good",
                improvements="Bad",
            )
        ]
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [MagicMock(id=user.id)]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="-1"),
    ):
        await ProjectsService(session).save_project_evaluation(1, body, user)


async def test_save_project_evaluation_creates_draft_without_unlock_check() -> None:
    """Draft submission (``submitted=False``) must save the row without triggering auto-unlock."""
    from datetime import UTC, datetime

    from models.course import EvaluationCriterion
    from models.project_evaluation import ProjectEvaluation
    from schemas.projects import EvaluationScoreDetail, ProjectEvaluationCreate

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.evaluation_criteria = [
        EvaluationCriterion(code="code_quality", description="Code Quality", max_score=25)
    ]
    session = MagicMock()
    session.commit = AsyncMock()
    user = _make_lecturer_user()

    evaluation = MagicMock(spec=ProjectEvaluation)
    evaluation.lecturer_id = 1
    evaluation.scores = [
        {
            "criterion_code": "code_quality",
            "score": 20,
            "strengths": "Good",
            "improvements": "Add more",
        }
    ]
    evaluation.updated_at = datetime(2025, 1, 1, tzinfo=UTC)
    evaluation.submitted = False

    body = ProjectEvaluationCreate(
        scores=[
            EvaluationScoreDetail(
                criterion_code="code_quality",
                score=20,
                strengths="Good",
                improvements="Add more",
            )
        ],
        submitted=False,
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [MagicMock(id=user.id)]},
        ),
        patch(
            "services.projects.db_upsert_project_evaluation",
            new_callable=AsyncMock,
            return_value=evaluation,
        ) as mock_upsert,
    ):
        result = await ProjectsService(session).save_project_evaluation(1, body, user)

    assert result.submitted is False
    mock_upsert.assert_called_once()
    # Only one commit — no auto-unlock triggered for drafts.
    session.commit.assert_called_once()


async def test_save_project_evaluation_final_submission_triggers_auto_unlock_check() -> None:
    """Final submission (``submitted=True``) must call ``_check_and_auto_unlock_project``."""
    from datetime import UTC, datetime

    from models.course import EvaluationCriterion
    from models.project_evaluation import ProjectEvaluation
    from schemas.projects import EvaluationScoreDetail, ProjectEvaluationCreate

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.evaluation_criteria = [
        EvaluationCriterion(code="code_quality", description="Code Quality", max_score=25)
    ]
    session = MagicMock()
    session.commit = AsyncMock()
    user = _make_lecturer_user()

    evaluation = MagicMock(spec=ProjectEvaluation)
    evaluation.lecturer_id = 1
    evaluation.scores = []
    evaluation.updated_at = datetime(2025, 1, 1, tzinfo=UTC)
    evaluation.submitted = True

    body = ProjectEvaluationCreate(
        scores=[
            EvaluationScoreDetail(
                criterion_code="code_quality",
                score=20,
                strengths="Good",
                improvements="Add more",
            )
        ],
        submitted=True,
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.auth.get_course_lecturers",
            new_callable=AsyncMock,
            return_value={10: [MagicMock(id=user.id)]},
        ),
        patch(
            "services.projects.db_upsert_project_evaluation",
            new_callable=AsyncMock,
            return_value=evaluation,
        ),
        patch(
            "services.projects._check_and_auto_unlock_project",
            new_callable=AsyncMock,
        ) as mock_check,
    ):
        result = await ProjectsService(session).save_project_evaluation(1, body, user)

    assert result.submitted is True
    mock_check.assert_called_once()
    # Two commits: one after evaluation insert, one after auto-unlock check.
    assert session.commit.call_count == 2


# ---------------------------------------------------------------------------
# _check_and_auto_unlock_project unit tests
# ---------------------------------------------------------------------------


async def test_auto_unlock_fires_when_all_submitted() -> None:
    """Auto-unlock must call ``db_unlock_project_results`` when all evaluations are complete."""
    from models.user import User

    project, course = _make_project_and_course()
    lecturer = MagicMock(spec=User)
    lecturer.email = "lecturer@tul.cz"
    member = MagicMock(spec=User)
    member.email = "student@tul.cz"
    session = MagicMock()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_lecturer_evaluation_statuses",
            new_callable=AsyncMock,
            return_value=[(lecturer, True)],  # 1 lecturer, submitted.
        ),
        patch(
            "services.projects.get_member_evaluation_statuses",
            new_callable=AsyncMock,
            return_value=[(member, True)],  # 1 member, submitted.
        ),
        patch(
            "services.projects.db_unlock_project_results",
            new_callable=AsyncMock,
        ) as mock_unlock,
        patch("services.projects.EmailSender"),  # Prevent real email side-effects.
        patch(
            "services.projects.get_settings",
            return_value=MagicMock(frontend_url="http://localhost:5173", app_env="local"),
        ),
    ):
        from services.projects import _check_and_auto_unlock_project

        await _check_and_auto_unlock_project(session, 1)

    mock_unlock.assert_called_once_with(session, 1)


async def test_auto_unlock_does_not_fire_when_not_all_lecturers_submitted() -> None:
    """Auto-unlock must not fire when not all lecturers have submitted."""
    from models.user import User

    project, course = _make_project_and_course()
    lecturer1 = MagicMock(spec=User)
    lecturer2 = MagicMock(spec=User)
    member = MagicMock(spec=User)
    session = MagicMock()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_lecturer_evaluation_statuses",
            new_callable=AsyncMock,
            # 2 lecturers: one submitted, one not.
            return_value=[(lecturer1, True), (lecturer2, False)],
        ),
        patch(
            "services.projects.get_member_evaluation_statuses",
            new_callable=AsyncMock,
            return_value=[(member, True)],
        ),
        patch(
            "services.projects.db_unlock_project_results",
            new_callable=AsyncMock,
        ) as mock_unlock,
    ):
        from services.projects import _check_and_auto_unlock_project

        await _check_and_auto_unlock_project(session, 1)

    mock_unlock.assert_not_called()


async def test_auto_unlock_does_not_fire_when_no_members() -> None:
    """Auto-unlock must not fire when there are no project members."""
    from models.user import User

    project, course = _make_project_and_course()
    lecturer = MagicMock(spec=User)
    session = MagicMock()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch(
            "services.projects.get_lecturer_evaluation_statuses",
            new_callable=AsyncMock,
            return_value=[(lecturer, True)],  # 1 lecturer submitted.
        ),
        patch(
            "services.projects.get_member_evaluation_statuses",
            new_callable=AsyncMock,
            return_value=[],  # No members.
        ),
        patch(
            "services.projects.db_unlock_project_results",
            new_callable=AsyncMock,
        ) as mock_unlock,
    ):
        from services.projects import _check_and_auto_unlock_project

        await _check_and_auto_unlock_project(session, 1)

    mock_unlock.assert_not_called()


# ---------------------------------------------------------------------------
# ProjectsService.get_course_evaluation_form unit tests
# ---------------------------------------------------------------------------


def _make_student_user(user_id: int = 5) -> MagicMock:
    """Return a mock STUDENT user with the specified id."""
    from models.user import User

    user = MagicMock(spec=User)
    user.id = user_id
    user.role = UserRole.STUDENT
    return user


async def test_get_course_evaluation_form_raises_when_project_not_found() -> None:
    """``get_course_evaluation_form`` must raise ``ProjectNotFoundError`` when project is absent."""
    from services.projects import ProjectNotFoundError

    session = MagicMock()
    user = _make_student_user()

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(ProjectNotFoundError),
    ):
        await ProjectsService(session).get_course_evaluation_form(99, user)


async def test_get_course_evaluation_form_raises_when_not_a_member() -> None:
    """``get_course_evaluation_form`` must raise ``PermissionDeniedError`` for non-members."""
    from services.projects import PermissionDeniedError

    project, course = _make_project_and_course()
    session = MagicMock()
    user = _make_student_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=False),
        pytest.raises(PermissionDeniedError),
    ):
        await ProjectsService(session).get_course_evaluation_form(1, user)


async def test_get_course_evaluation_form_raises_for_non_student() -> None:
    """``get_course_evaluation_form`` must raise ``PermissionDeniedError`` for non-students."""
    from services.projects import PermissionDeniedError

    project, course = _make_project_and_course()
    session = MagicMock()
    lecturer = _make_lecturer_user()

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        pytest.raises(PermissionDeniedError, match="Only students"),
    ):
        await ProjectsService(session).get_course_evaluation_form(1, lecturer)


async def test_get_course_evaluation_form_returns_no_draft_when_none_exists() -> None:
    """``get_course_evaluation_form`` must return ``current_evaluation=None`` with no draft."""

    project, course = _make_project_and_course()
    course.peer_bonus_budget = None
    project.results_unlocked = False

    session = MagicMock()
    user = _make_student_user(user_id=5)

    from models.user import User

    teammate = MagicMock(spec=User)
    teammate.id = 7
    teammate.name = "Bob"
    teammate.github_alias = None
    teammate.email = "bob@tul.cz"

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await ProjectsService(session).get_course_evaluation_form(1, user)

    assert result.current_evaluation is None
    assert result.authored_peer_feedback == []
    assert len(result.teammates) == 1
    assert result.teammates[0].id == 7
    assert result.results_unlocked is False


async def test_get_course_evaluation_form_returns_draft_when_exists() -> None:
    """``get_course_evaluation_form`` must include the existing draft evaluation."""
    from datetime import UTC, datetime

    from models.course_evaluation import CourseEvaluation

    project, course = _make_project_and_course()
    course.peer_bonus_budget = 10
    project.results_unlocked = False

    session = MagicMock()
    user = _make_student_user(user_id=5)

    existing_eval = MagicMock(spec=CourseEvaluation)
    existing_eval.id = 1
    existing_eval.student_id = 5
    existing_eval.rating = 4
    existing_eval.strengths = "Good"
    existing_eval.improvements = "Better"
    existing_eval.submitted = False
    existing_eval.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: []},
        ),
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=existing_eval,
        ),
        patch(
            "services.projects.get_peer_feedback_authored",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await ProjectsService(session).get_course_evaluation_form(1, user)

    assert result.current_evaluation is not None
    assert result.current_evaluation.rating == 4
    assert result.peer_bonus_budget == 10


# ---------------------------------------------------------------------------
# ProjectsService.save_course_evaluation unit tests
# ---------------------------------------------------------------------------


async def test_save_course_evaluation_raises_when_project_not_found() -> None:
    """``save_course_evaluation`` must raise ``ProjectNotFoundError`` when project is absent."""
    from schemas.projects import CourseEvaluationUpsert
    from services.projects import ProjectNotFoundError

    session = MagicMock()
    user = _make_student_user()
    body = CourseEvaluationUpsert(rating=4)

    with (
        patch("services.projects.db_get_project", new_callable=AsyncMock, return_value=None),
        pytest.raises(ProjectNotFoundError),
    ):
        await ProjectsService(session).save_course_evaluation(99, body, user)


async def test_save_course_evaluation_raises_permission_error_for_non_member() -> None:
    """``save_course_evaluation`` must raise ``PermissionDeniedError`` for non-members."""
    from schemas.projects import CourseEvaluationUpsert
    from services.projects import PermissionDeniedError

    project, course = _make_project_and_course()
    session = MagicMock()
    user = _make_student_user()
    body = CourseEvaluationUpsert(rating=3)

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=False),
        pytest.raises(PermissionDeniedError),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_for_non_student() -> None:
    """``save_course_evaluation`` must raise ``PermissionDeniedError`` for non-students."""
    from schemas.projects import CourseEvaluationUpsert
    from services.projects import PermissionDeniedError

    project, course = _make_project_and_course()
    session = MagicMock()
    lecturer = _make_lecturer_user()
    body = CourseEvaluationUpsert(rating=3)

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        pytest.raises(PermissionDeniedError, match="Only students"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, lecturer)


async def test_save_course_evaluation_raises_conflict_when_results_unlocked() -> None:
    """``save_course_evaluation`` must raise ``EvaluationConflictError`` if results are unlocked."""
    from schemas.projects import CourseEvaluationUpsert
    from services.projects import EvaluationConflictError

    project, course = _make_project_and_course()
    project.results_unlocked = True
    session = MagicMock()
    user = _make_student_user()
    body = CourseEvaluationUpsert(rating=3)

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        pytest.raises(EvaluationConflictError),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_when_submitted_without_rating() -> None:
    """``save_course_evaluation`` must raise when ``submitted=True`` but rating is None."""
    from schemas.projects import CourseEvaluationUpsert
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    session = MagicMock()
    user = _make_student_user(user_id=5)

    body = CourseEvaluationUpsert(submitted=True)  # rating defaults to None

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        pytest.raises(InvalidEvaluationDataError, match="[Rr]ating"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_invalid_data_for_unknown_recipient() -> None:
    """``save_course_evaluation`` must raise ``InvalidEvaluationDataError`` for bad recipient."""
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    session = MagicMock()
    user = _make_student_user(user_id=5)

    teammate = MagicMock(spec=User)
    teammate.id = 7

    body = CourseEvaluationUpsert(
        rating=4,
        peer_feedback=[PeerFeedbackInput(receiving_student_id=999, bonus_points=0)],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="recipient"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_for_peer_feedback_on_individual_course() -> None:
    """``save_course_evaluation`` must reject peer feedback on individual courses."""
    from models.course import ProjectType as PT
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.project_type = PT.INDIVIDUAL
    session = MagicMock()
    user = _make_student_user(user_id=5)

    body = CourseEvaluationUpsert(
        rating=4,
        peer_feedback=[PeerFeedbackInput(receiving_student_id=7, bonus_points=0)],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        pytest.raises(InvalidEvaluationDataError, match="team courses"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_for_duplicate_recipient_ids() -> None:
    """``save_course_evaluation`` must raise ``InvalidEvaluationDataError`` for duplicate IDs."""
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    session = MagicMock()
    user = _make_student_user(user_id=5)

    teammate = MagicMock(spec=User)
    teammate.id = 7

    body = CourseEvaluationUpsert(
        rating=4,
        peer_feedback=[
            PeerFeedbackInput(receiving_student_id=7, bonus_points=0),
            PeerFeedbackInput(receiving_student_id=7, bonus_points=0),
        ],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="[Dd]uplicate"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_when_per_recipient_bonus_too_high() -> None:
    """``save_course_evaluation`` must raise ``InvalidEvaluationDataError`` for over-cap bonus."""
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.peer_bonus_budget = 10
    session = MagicMock()
    user = _make_student_user(user_id=5)

    teammate = MagicMock(spec=User)
    teammate.id = 7

    # 25 > 2 × 10 = 20 — must be rejected.
    body = CourseEvaluationUpsert(
        rating=4,
        submitted=False,
        peer_feedback=[PeerFeedbackInput(receiving_student_id=7, bonus_points=25)],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="2 × peer_bonus_budget"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_for_negative_bonus_points() -> None:
    """``save_course_evaluation`` must raise ``InvalidEvaluationDataError`` for negative bonus."""
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.peer_bonus_budget = 10
    session = MagicMock()
    user = _make_student_user(user_id=5)

    teammate = MagicMock(spec=User)
    teammate.id = 7

    body = CourseEvaluationUpsert(
        rating=4,
        peer_feedback=[PeerFeedbackInput(receiving_student_id=7, bonus_points=-1)],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="non-negative"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_when_bonus_nonzero_without_budget() -> None:
    """``save_course_evaluation`` must raise when bonus_points > 0 and no peer-bonus scheme."""
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.peer_bonus_budget = None
    session = MagicMock()
    user = _make_student_user(user_id=5)

    teammate = MagicMock(spec=User)
    teammate.id = 7

    body = CourseEvaluationUpsert(
        rating=4,
        peer_feedback=[PeerFeedbackInput(receiving_student_id=7, bonus_points=5)],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="no peer-bonus scheme"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_raises_invalid_data_when_bonus_budget_not_met() -> None:
    """``save_course_evaluation`` must raise ``InvalidEvaluationDataError`` on wrong bonus total."""
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert, PeerFeedbackInput
    from services.projects import InvalidEvaluationDataError

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.peer_bonus_budget = 10
    session = MagicMock()
    user = _make_student_user(user_id=5)

    teammate = MagicMock(spec=User)
    teammate.id = 7

    body = CourseEvaluationUpsert(
        rating=4,
        submitted=True,
        peer_feedback=[PeerFeedbackInput(receiving_student_id=7, bonus_points=3)],
    )

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        pytest.raises(InvalidEvaluationDataError, match="budget"),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)


async def test_save_course_evaluation_triggers_auto_unlock_on_final_submission() -> None:
    """``save_course_evaluation`` must call ``_check_and_auto_unlock_project`` when submitted."""
    from datetime import UTC, datetime

    from models.course_evaluation import CourseEvaluation
    from models.user import User
    from schemas.projects import CourseEvaluationUpsert

    project, course = _make_project_and_course()
    project.results_unlocked = False
    course.peer_bonus_budget = None
    session = MagicMock()
    session.commit = AsyncMock()
    user = _make_student_user(user_id=5)

    existing_eval = MagicMock(spec=CourseEvaluation)
    existing_eval.id = 1
    existing_eval.student_id = 5
    existing_eval.rating = 3
    existing_eval.strengths = None
    existing_eval.improvements = None
    existing_eval.submitted = True
    existing_eval.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

    body = CourseEvaluationUpsert(rating=3, submitted=True)

    teammate = MagicMock(spec=User)
    teammate.id = 7
    teammate.name = "Bob"
    teammate.github_alias = None
    teammate.email = "bob@tul.cz"

    with (
        patch(
            "services.projects.db_get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        patch("services.projects.is_project_member", new_callable=AsyncMock, return_value=True),
        patch(
            "services.projects.get_project_members",
            new_callable=AsyncMock,
            return_value={1: [teammate]},
        ),
        patch(
            "services.projects.upsert_course_evaluation",
            new_callable=AsyncMock,
            return_value=existing_eval,
        ),
        patch(
            "services.projects.replace_peer_feedback",
            new_callable=AsyncMock,
        ),
        patch(
            "services.projects._check_and_auto_unlock_project",
            new_callable=AsyncMock,
        ) as mock_unlock,
        patch(
            "services.projects.get_course_evaluation_by_student",
            new_callable=AsyncMock,
            return_value=existing_eval,
        ),
        patch(
            "services.projects.get_peer_feedback_authored",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        await ProjectsService(session).save_course_evaluation(1, body, user)

    mock_unlock.assert_called_once_with(session, 1)
