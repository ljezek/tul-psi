from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.course import CourseTerm
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
