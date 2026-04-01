from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from api.courses import get_courses_service
from main import app
from models.course import CourseTerm, ProjectType
from schemas.courses import CourseDetail, CourseListItem, CourseStats
from schemas.projects import LecturerPublic
from services.courses import CoursesService

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_LECTURER = LecturerPublic(name="Jan Novák", github_alias="jnovak")

_STATS = CourseStats(
    project_count=3,
    academic_years=[2024, 2025],
    lecturer_names=["Jan Novák"],
)

_COURSE_LIST_ITEM = CourseListItem(
    id=1,
    code="PSI",
    name="Projektový seminář informatiky",
    stats=_STATS,
)

_COURSE_DETAIL = CourseDetail(
    id=1,
    code="PSI",
    name="Projektový seminář informatiky",
    syllabus="Course syllabus text.",
    term=CourseTerm.WINTER,
    project_type=ProjectType.TEAM,
    min_score=50,
    peer_bonus_budget=10,
    evaluation_criteria=[{"code": "code_quality", "description": "Code Quality", "max_score": 25}],
    links=[{"label": "eLearning", "url": "https://elearning.example.com"}],
    lecturers=[_LECTURER],
)


def _make_service(
    courses: list[CourseListItem] | None = None,
    detail: CourseDetail | None = None,
) -> CoursesService:
    """Return a mock ``CoursesService`` configured with the given return values."""
    service = MagicMock(spec=CoursesService)
    service.get_courses = AsyncMock(return_value=courses or [])
    service.get_course = AsyncMock(return_value=detail)
    return service


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Generator[None, None, None]:
    """Reset FastAPI dependency overrides after every test to ensure isolation."""
    yield
    app.dependency_overrides.pop(get_courses_service, None)


# ---------------------------------------------------------------------------
# GET /api/v1/courses — basic response shape
# ---------------------------------------------------------------------------


async def test_list_courses_returns_200(client: AsyncClient) -> None:
    """GET /api/v1/courses must return HTTP 200."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service([_COURSE_LIST_ITEM])
    response = await client.get("/api/v1/courses")
    assert response.status_code == 200


async def test_list_courses_returns_list(client: AsyncClient) -> None:
    """GET /api/v1/courses must return a JSON array."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service([_COURSE_LIST_ITEM])
    response = await client.get("/api/v1/courses")
    assert isinstance(response.json(), list)


async def test_list_courses_empty_when_no_courses(client: AsyncClient) -> None:
    """GET /api/v1/courses must return an empty array when there are no courses."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service([])
    response = await client.get("/api/v1/courses")
    assert response.json() == []


async def test_list_courses_response_schema(client: AsyncClient) -> None:
    """GET /api/v1/courses items must match the full ``CourseListItem`` shape."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service([_COURSE_LIST_ITEM])
    response = await client.get("/api/v1/courses")
    assert response.json()[0] == _COURSE_LIST_ITEM.model_dump(mode="json")


async def test_list_courses_stats_fields_present(client: AsyncClient) -> None:
    """Each item in GET /api/v1/courses must include project_count, academic_years, lecturer_names.

    These are the three aggregated stats fields that distinguish the list representation
    from a bare course record.
    """
    app.dependency_overrides[get_courses_service] = lambda: _make_service([_COURSE_LIST_ITEM])
    response = await client.get("/api/v1/courses")
    stats = response.json()[0]["stats"]
    assert "project_count" in stats
    assert "academic_years" in stats
    assert "lecturer_names" in stats


# ---------------------------------------------------------------------------
# GET /api/v1/courses — error handling
# ---------------------------------------------------------------------------


async def test_list_courses_returns_500_on_service_error(client: AsyncClient) -> None:
    """A service-layer exception on GET /api/v1/courses must result in HTTP 500."""
    mock_service = _make_service([])
    mock_service.get_courses.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    response = await client.get("/api/v1/courses")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/courses/{course_id} — basic response shape
# ---------------------------------------------------------------------------


async def test_get_course_returns_200(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} must return HTTP 200 when the course exists."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    response = await client.get("/api/v1/courses/1")
    assert response.status_code == 200


async def test_get_course_returns_detail_schema(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} response must match the full ``CourseDetail`` shape."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    response = await client.get("/api/v1/courses/1")
    assert response.json() == _COURSE_DETAIL.model_dump(mode="json")


async def test_get_course_returns_404_when_not_found(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} must return HTTP 404 when the course does not exist."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=None)
    response = await client.get("/api/v1/courses/999")
    assert response.status_code == 404


async def test_get_course_forwards_id_to_service(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} must pass the path parameter id to the service."""
    mock_service = _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    await client.get("/api/v1/courses/42")
    mock_service.get_course.assert_called_once_with(42)


async def test_get_course_returns_500_on_service_error(client: AsyncClient) -> None:
    """A service-layer exception on GET /api/v1/courses/{id} must result in HTTP 500."""
    mock_service = _make_service()
    mock_service.get_course.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    response = await client.get("/api/v1/courses/1")
    assert response.status_code == 500
