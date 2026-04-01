from __future__ import annotations

# TODO: Mirror source tree layout in tests/ (e.g. tests/api/, tests/services/, tests/db/)
#       to avoid a single flat test folder becoming unwieldy as coverage grows.
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from api.projects import get_projects_service
from main import app
from models.course import CourseTerm, ProjectType
from schemas.projects import CoursePublic, LecturerPublic, MemberPublic, ProjectPublic
from services.projects import ProjectsService

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_LECTURER = LecturerPublic(name="Jan Novák", github_alias="jnovak")

_COURSE = CoursePublic(
    code="PSI",
    name="Projektový seminář informatiky",
    syllabus=None,
    term=CourseTerm.WINTER,
    project_type=ProjectType.TEAM,
    min_score=50,
    peer_bonus_budget=None,
    evaluation_criteria=[],
    links=[],
    lecturers=[_LECTURER],
)

_MEMBER = MemberPublic(id=5, github_alias="jnovak", name="Jan Novák")

_PROJECT = ProjectPublic(
    id=1,
    title="Student Projects Catalogue",
    description="A catalogue of student projects.",
    github_url="https://github.com/example/spc",
    live_url="https://spc.example.com",
    technologies=["Python", "FastAPI", "React"],
    academic_year=2025,
    course=_COURSE,
    members=[_MEMBER],
)


def _make_service(projects: list[ProjectPublic] | None = None) -> ProjectsService:
    """Return a mock ``ProjectsService`` configured to return ``projects``."""
    service = MagicMock(spec=ProjectsService)
    service.get_projects = AsyncMock(return_value=projects or [])
    service.get_project = AsyncMock(return_value=None)
    return service


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Generator[None, None, None]:
    """Reset FastAPI dependency overrides after every test to ensure isolation."""
    yield
    app.dependency_overrides.pop(get_projects_service, None)


# ---------------------------------------------------------------------------
# Basic response shape
# ---------------------------------------------------------------------------


async def test_list_projects_returns_200(client: AsyncClient) -> None:
    """GET /api/v1/projects must return HTTP 200."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([_PROJECT])
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200


async def test_list_projects_returns_list(client: AsyncClient) -> None:
    """GET /api/v1/projects must return a JSON array."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([_PROJECT])
    response = await client.get("/api/v1/projects")
    assert isinstance(response.json(), list)


async def test_list_projects_empty_when_no_results(client: AsyncClient) -> None:
    """GET /api/v1/projects must return an empty array when no projects match."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([])
    response = await client.get("/api/v1/projects")
    assert response.json() == []


async def test_list_projects_response_schema(client: AsyncClient) -> None:
    """GET /api/v1/projects response items must match the full ``ProjectPublic`` shape."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([_PROJECT])
    response = await client.get("/api/v1/projects")
    assert response.json()[0] == _PROJECT.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Query parameter forwarding
# ---------------------------------------------------------------------------


async def test_list_projects_no_params_passes_defaults_to_service(client: AsyncClient) -> None:
    """Calling with no query parameters must pass all-None defaults to the service."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects")
    mock_service.get_projects.assert_called_once_with(
        q=None, course=None, year=None, term=None, lecturer=None, technology=None
    )


async def test_list_projects_all_params_forwarded_to_service(client: AsyncClient) -> None:
    """All query parameters must be correctly forwarded to ``service.get_projects``."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get(
        "/api/v1/projects?q=test&course=PSI&year=2025&term=WINTER&lecturer=Novak&technology=FastAPI"
    )
    mock_service.get_projects.assert_called_once_with(
        q="test",
        course="PSI",
        year=2025,
        term=CourseTerm.WINTER,
        lecturer="Novak",
        technology="FastAPI",
    )


async def test_list_projects_invalid_term_returns_422(client: AsyncClient) -> None:
    """An unrecognised ``term`` value must yield HTTP 422 (Unprocessable Entity)."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([])
    response = await client.get("/api/v1/projects?term=SPRING")
    assert response.status_code == 422


async def test_list_projects_invalid_year_returns_422(client: AsyncClient) -> None:
    """A non-integer ``year`` value must yield HTTP 422 (Unprocessable Entity)."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([])
    response = await client.get("/api/v1/projects?year=notanumber")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


async def test_list_projects_returns_500_on_service_error(client: AsyncClient) -> None:
    """A service-layer exception must result in HTTP 500."""
    mock_service = _make_service([])
    mock_service.get_projects.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    response = await client.get("/api/v1/projects")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# ProjectsService unit tests
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
# DB layer unit tests
# ---------------------------------------------------------------------------


async def test_get_project_members_returns_empty_dict_for_empty_ids() -> None:
    """``get_project_members`` must short-circuit and return ``{}`` for an empty id list."""
    from db.projects import get_project_members

    session = AsyncMock()
    result = await get_project_members(session, [])
    assert result == {}
    session.execute.assert_not_called()


async def test_get_course_lecturers_returns_empty_dict_for_empty_ids() -> None:
    """``get_course_lecturers`` must short-circuit and return ``{}`` for an empty id list."""
    from db.projects import get_course_lecturers

    session = AsyncMock()
    result = await get_course_lecturers(session, [])
    assert result == {}
    session.execute.assert_not_called()


def test_escape_like_escapes_wildcards() -> None:
    """``_escape_like`` must escape ``%``, ``_``, and backslash characters."""
    from db.projects import _escape_like

    assert _escape_like("100%") == "100\\%"
    assert _escape_like("user_name") == "user\\_name"
    assert _escape_like("back\\slash") == "back\\\\slash"


# ---------------------------------------------------------------------------
# GET /projects/{project_id} — endpoint tests
# ---------------------------------------------------------------------------


async def test_get_project_returns_200(client: AsyncClient) -> None:
    """GET /api/v1/projects/{id} must return HTTP 200 when the project exists."""
    mock_service = _make_service()
    mock_service.get_project = AsyncMock(return_value=_PROJECT)
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    response = await client.get("/api/v1/projects/1")
    assert response.status_code == 200


async def test_get_project_returns_project_schema(client: AsyncClient) -> None:
    """GET /api/v1/projects/{id} response must match the full ``ProjectPublic`` shape."""
    mock_service = _make_service()
    mock_service.get_project = AsyncMock(return_value=_PROJECT)
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    response = await client.get("/api/v1/projects/1")
    assert response.json() == _PROJECT.model_dump(mode="json")


async def test_get_project_returns_404_when_not_found(client: AsyncClient) -> None:
    """GET /api/v1/projects/{id} must return HTTP 404 when the project does not exist."""
    mock_service = _make_service()
    mock_service.get_project = AsyncMock(return_value=None)
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    response = await client.get("/api/v1/projects/999")
    assert response.status_code == 404


async def test_get_project_returns_500_on_service_error(client: AsyncClient) -> None:
    """A service-layer exception on GET /api/v1/projects/{id} must result in HTTP 500."""
    mock_service = _make_service()
    mock_service.get_project = AsyncMock(side_effect=RuntimeError("db failure"))
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    response = await client.get("/api/v1/projects/1")
    assert response.status_code == 500


async def test_get_project_forwards_id_to_service(client: AsyncClient) -> None:
    """GET /api/v1/projects/{id} must pass the path parameter id to the service."""
    mock_service = _make_service()
    mock_service.get_project = AsyncMock(return_value=_PROJECT)
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects/42")
    mock_service.get_project.assert_called_once_with(42)


# ---------------------------------------------------------------------------
# ProjectsService.get_project unit tests
# ---------------------------------------------------------------------------


async def test_service_get_project_returns_none_when_not_found() -> None:
    """``ProjectsService.get_project`` must return ``None`` when the DB row is absent."""
    session = MagicMock()
    with patch("services.projects.get_project", new_callable=AsyncMock, return_value=None):
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
            "services.projects.get_project",
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
    """``ProjectsService.get_project`` must raise ``ValueError`` when the returned project has no id."""
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
            "services.projects.get_project",
            new_callable=AsyncMock,
            return_value=(project, course),
        ),
        pytest.raises(ValueError, match="no id"),
    ):
        await ProjectsService(session).get_project(1)
