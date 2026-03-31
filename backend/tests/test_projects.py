from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient

from api.projects import get_projects_service
from main import app
from models.course import CourseTerm
from schemas.projects import CoursePublic, MemberPublic, ProjectPublic
from services.projects import ProjectsService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_COURSE = CoursePublic(
    id=1, code="PSI", name="Projektový seminář informatiky", term=CourseTerm.WINTER
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
    service.get_projects.return_value = projects or []
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
    """GET /api/v1/projects response items must include all required fields."""
    app.dependency_overrides[get_projects_service] = lambda: _make_service([_PROJECT])
    response = await client.get("/api/v1/projects")
    item = response.json()[0]
    assert item["id"] == 1
    assert item["title"] == "Student Projects Catalogue"
    assert item["technologies"] == ["Python", "FastAPI", "React"]
    assert item["academic_year"] == 2025
    assert item["course"]["code"] == "PSI"
    assert item["course"]["term"] == "WINTER"
    assert item["members"][0]["name"] == "Jan Novák"


# ---------------------------------------------------------------------------
# Query parameter forwarding
# ---------------------------------------------------------------------------


async def test_list_projects_passes_q_to_service(client: AsyncClient) -> None:
    """The ``q`` query parameter must be forwarded to ``service.get_projects``."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects?q=catalogue")
    mock_service.get_projects.assert_called_once_with(
        q="catalogue",
        course=None,
        year=None,
        term=None,
        lecturer=None,
        technology=None,
    )


async def test_list_projects_passes_course_to_service(client: AsyncClient) -> None:
    """The ``course`` query parameter must be forwarded to ``service.get_projects``."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects?course=PSI")
    mock_service.get_projects.assert_called_once_with(
        q=None,
        course="PSI",
        year=None,
        term=None,
        lecturer=None,
        technology=None,
    )


async def test_list_projects_passes_year_to_service(client: AsyncClient) -> None:
    """The ``year`` query parameter must be forwarded as an integer."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects?year=2025")
    mock_service.get_projects.assert_called_once_with(
        q=None,
        course=None,
        year=2025,
        term=None,
        lecturer=None,
        technology=None,
    )


async def test_list_projects_passes_term_to_service(client: AsyncClient) -> None:
    """The ``term`` query parameter must be forwarded as a ``CourseTerm`` enum value."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects?term=WINTER")
    mock_service.get_projects.assert_called_once_with(
        q=None,
        course=None,
        year=None,
        term=CourseTerm.WINTER,
        lecturer=None,
        technology=None,
    )


async def test_list_projects_passes_lecturer_to_service(client: AsyncClient) -> None:
    """The ``lecturer`` query parameter must be forwarded to ``service.get_projects``."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects?lecturer=Novak")
    mock_service.get_projects.assert_called_once_with(
        q=None,
        course=None,
        year=None,
        term=None,
        lecturer="Novak",
        technology=None,
    )


async def test_list_projects_passes_technology_to_service(client: AsyncClient) -> None:
    """The ``technology`` query parameter must be forwarded to ``service.get_projects``."""
    mock_service = _make_service([])
    app.dependency_overrides[get_projects_service] = lambda: mock_service
    await client.get("/api/v1/projects?technology=FastAPI")
    mock_service.get_projects.assert_called_once_with(
        q=None,
        course=None,
        year=None,
        term=None,
        lecturer=None,
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
