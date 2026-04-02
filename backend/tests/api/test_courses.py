from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from api.courses import get_courses_service
from api.deps import get_current_user
from main import app
from models.course import CourseTerm, ProjectType
from models.user import UserRole
from schemas.courses import CourseDetail, CourseEvaluationPublic, CourseListItem, CourseStats
from schemas.projects import LecturerPublic
from services.courses import CoursesService

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_LECTURER = LecturerPublic(name="Jan Novák", github_alias="jnovak")
_LECTURER_WITH_EMAIL = LecturerPublic(
    name="Jan Novák",
    github_alias="jnovak",
    email="jan.novak@tul.cz",
)

_STATS = CourseStats(
    project_count=3,
    academic_years=[2024, 2025],
)

_COURSE_LIST_ITEM = CourseListItem(
    id=1,
    code="PSI",
    name="Projektový seminář informatiky",
    syllabus="Course syllabus.",
    lecturer_names=["Jan Novák"],
    stats=_STATS,
)

_NOW = datetime(2025, 1, 15, 12, 0, tzinfo=UTC)

_EVALUATION = CourseEvaluationPublic(
    id=1,
    project_id=10,
    student_id=5,
    rating=4,
    strengths="Great course.",
    improvements="More exercises.",
    published=True,
    submitted_at=_NOW,
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
    course_evaluations=None,
)

_COURSE_DETAIL_WITH_EVALUATIONS = CourseDetail(
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
    lecturers=[_LECTURER_WITH_EMAIL],
    course_evaluations=[_EVALUATION],
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


def _make_user(role: UserRole = UserRole.ADMIN) -> MagicMock:
    """Return a mock ``User`` with the specified role."""
    user = MagicMock()
    user.role = role
    user.id = 99
    return user


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Generator[None, None, None]:
    """Reset FastAPI dependency overrides after every test to ensure isolation.

    ``get_current_user`` defaults to returning ``None`` (unauthenticated) so that
    tests that do not exercise auth behaviour do not need to override it manually.
    """
    app.dependency_overrides[get_current_user] = lambda: None
    yield
    app.dependency_overrides.pop(get_courses_service, None)
    app.dependency_overrides.pop(get_current_user, None)


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


async def test_list_courses_item_has_syllabus_and_lecturer_names(client: AsyncClient) -> None:
    """Each item in GET /api/v1/courses must include syllabus and lecturer_names at top level."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service([_COURSE_LIST_ITEM])
    response = await client.get("/api/v1/courses")
    item = response.json()[0]
    assert "syllabus" in item
    assert "lecturer_names" in item
    # Lecturer names must be at the top level, not nested inside stats.
    assert "lecturer_names" not in item["stats"]


async def test_list_courses_stats_has_no_lecturer_names(client: AsyncClient) -> None:
    """``stats`` in GET /api/v1/courses must not contain ``lecturer_names``."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service([_COURSE_LIST_ITEM])
    response = await client.get("/api/v1/courses")
    stats = response.json()[0]["stats"]
    assert "project_count" in stats
    assert "academic_years" in stats
    assert "lecturer_names" not in stats


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
    mock_service.get_course.assert_called_once_with(42, current_user=None)


async def test_get_course_returns_500_on_service_error(client: AsyncClient) -> None:
    """A service-layer exception on GET /api/v1/courses/{id} must result in HTTP 500."""
    mock_service = _make_service()
    mock_service.get_course.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    response = await client.get("/api/v1/courses/1")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/courses/{course_id} — authenticated behaviour
# ---------------------------------------------------------------------------


async def test_get_course_passes_current_user_to_service(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} must forward the resolved current_user to the service."""
    mock_user = _make_user(UserRole.ADMIN)
    mock_service = _make_service(detail=_COURSE_DETAIL_WITH_EVALUATIONS)
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    await client.get("/api/v1/courses/1")
    mock_service.get_course.assert_called_once_with(1, current_user=mock_user)


async def test_get_course_returns_evaluations_for_admin(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} for an admin must include course_evaluations."""
    mock_user = _make_user(UserRole.ADMIN)
    app.dependency_overrides[get_courses_service] = lambda: _make_service(
        detail=_COURSE_DETAIL_WITH_EVALUATIONS
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    response = await client.get("/api/v1/courses/1")
    assert response.json()["course_evaluations"] is not None
    assert len(response.json()["course_evaluations"]) == 1


async def test_get_course_evaluations_null_for_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} without a session must return course_evaluations as null."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: None
    response = await client.get("/api/v1/courses/1")
    assert response.json()["course_evaluations"] is None
