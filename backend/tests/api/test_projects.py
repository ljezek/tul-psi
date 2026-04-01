from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from api.deps import get_current_user
from api.projects import get_projects_service
from main import app
from models.course import CourseTerm, ProjectType
from models.user import UserRole
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
    service.get_project_detail = AsyncMock(return_value=None)
    return service


def _make_authenticated_user(role: UserRole = UserRole.STUDENT) -> MagicMock:
    """Return a mock ``User`` object for the given *role*."""
    from models.user import User

    user = MagicMock(spec=User)
    user.id = 99
    user.email = "test@tul.cz"
    user.name = "Test User"
    user.role = role
    return user


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Generator[None, None, None]:
    """Reset FastAPI dependency overrides after every test to ensure isolation.

    Sets ``get_current_user`` to return ``None`` by default for backward compatibility
    with existing unauthenticated tests.  Tests that need an authenticated user
    override ``get_current_user`` explicitly before making their request.
    """
    app.dependency_overrides[get_current_user] = lambda: None
    yield
    app.dependency_overrides.pop(get_projects_service, None)
    app.dependency_overrides.pop(get_current_user, None)


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
# GET /projects/{project_id} — authenticated endpoint tests
# ---------------------------------------------------------------------------


async def test_get_project_authenticated_calls_get_project_detail(client: AsyncClient) -> None:
    """Authenticated requests to GET /api/v1/projects/{id} must call ``get_project_detail``."""
    from schemas.projects import CourseDetail, LecturerDetail, MemberDetail, ProjectDetail

    user = _make_authenticated_user()
    mock_service = _make_service()
    detail = ProjectDetail(
        id=1,
        title="Test Project",
        description=None,
        github_url=None,
        live_url=None,
        technologies=[],
        academic_year=2025,
        results_unlocked=False,
        course=CourseDetail(
            code="PSI",
            name="PSI Course",
            syllabus=None,
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            peer_bonus_budget=None,
            evaluation_criteria=[],
            links=[],
            lecturers=[LecturerDetail(name="Lect", github_alias=None, email="lect@tul.cz")],
        ),
        members=[MemberDetail(id=5, github_alias=None, name="Alice", email="alice@tul.cz")],
    )
    mock_service.get_project_detail = AsyncMock(return_value=detail)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.get("/api/v1/projects/1")

    assert response.status_code == 200
    mock_service.get_project_detail.assert_called_once_with(1, user)
    mock_service.get_project.assert_not_called()


async def test_get_project_authenticated_response_includes_emails(client: AsyncClient) -> None:
    """Authenticated response must include ``results_unlocked``, lecturer e-mail, member e-mail."""
    from schemas.projects import CourseDetail, LecturerDetail, MemberDetail, ProjectDetail

    user = _make_authenticated_user(UserRole.STUDENT)
    mock_service = _make_service()
    detail = ProjectDetail(
        id=1,
        title="Test Project",
        description=None,
        github_url=None,
        live_url=None,
        technologies=[],
        academic_year=2025,
        results_unlocked=True,
        course=CourseDetail(
            code="PSI",
            name="PSI Course",
            syllabus=None,
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            peer_bonus_budget=None,
            evaluation_criteria=[],
            links=[],
            lecturers=[LecturerDetail(name="Lect", github_alias=None, email="lect@tul.cz")],
        ),
        members=[MemberDetail(id=5, github_alias=None, name="Alice", email="alice@tul.cz")],
    )
    mock_service.get_project_detail = AsyncMock(return_value=detail)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.get("/api/v1/projects/1")

    body = response.json()
    assert body["results_unlocked"] is True
    assert body["course"]["lecturers"][0]["email"] == "lect@tul.cz"
    assert body["members"][0]["email"] == "alice@tul.cz"


async def test_get_project_authenticated_404_when_not_found(client: AsyncClient) -> None:
    """Authenticated GET /api/v1/projects/{id} must return 404 when no project exists."""
    user = _make_authenticated_user()
    mock_service = _make_service()
    mock_service.get_project_detail = AsyncMock(return_value=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.get("/api/v1/projects/999")

    assert response.status_code == 404


async def test_get_project_authenticated_500_on_service_error(client: AsyncClient) -> None:
    """Authenticated GET /api/v1/projects/{id} must return 500 on service exception."""
    user = _make_authenticated_user()
    mock_service = _make_service()
    mock_service.get_project_detail = AsyncMock(side_effect=RuntimeError("db failure"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.get("/api/v1/projects/1")

    assert response.status_code == 500
