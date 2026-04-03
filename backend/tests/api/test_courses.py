from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from api.courses import get_courses_service, get_projects_service
from api.deps import get_current_user, get_optional_current_user
from main import app
from models.course import CourseTerm, ProjectType
from models.user import UserRole
from schemas.courses import (
    CourseDetail,
    CourseEvaluationPublic,
    CourseEvaluationSummary,
    CourseLecturerPublic,
    CourseListItem,
    CourseStats,
    CriterionScoreSummary,
    EvaluationOverviewResponse,
    ProjectEvaluationSummary,
    ProjectOverviewItem,
    ReceivedPeerFeedback,
    StudentBonusSummary,
)
from schemas.projects import CoursePublic, LecturerPublic, ProjectPublic
from services.courses import (
    CourseLecturerAlreadyAssignedError,
    CourseLecturerNotAssignedError,
    CourseNotFoundError,
    CoursePermissionError,
    CoursesService,
)
from services.projects import ProjectsService

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
    submitted=True,
    updated_at=_NOW,
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
    service.create_course = AsyncMock(return_value=detail)
    service.update_course = AsyncMock(return_value=detail)
    service.add_lecturer = AsyncMock(return_value=None)
    service.remove_lecturer = AsyncMock(return_value=None)
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

    ``get_optional_current_user`` defaults to returning ``None`` (unauthenticated)
    so that tests that do not exercise auth behaviour do not need to override it
    manually.  ``get_current_user`` is also pre-set to ``None`` to keep any tests
    that still reference the strict variant from accidentally hitting the real
    dependency.
    """
    app.dependency_overrides[get_optional_current_user] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: None
    yield
    app.dependency_overrides.pop(get_courses_service, None)
    app.dependency_overrides.pop(get_projects_service, None)
    app.dependency_overrides.pop(get_optional_current_user, None)
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
    app.dependency_overrides[get_optional_current_user] = lambda: mock_user
    await client.get("/api/v1/courses/1")
    mock_service.get_course.assert_called_once_with(1, current_user=mock_user)


async def test_get_course_returns_evaluations_for_admin(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} for an admin must include course_evaluations."""
    mock_user = _make_user(UserRole.ADMIN)
    app.dependency_overrides[get_courses_service] = lambda: _make_service(
        detail=_COURSE_DETAIL_WITH_EVALUATIONS
    )
    app.dependency_overrides[get_optional_current_user] = lambda: mock_user
    response = await client.get("/api/v1/courses/1")
    assert response.json()["course_evaluations"] is not None
    assert len(response.json()["course_evaluations"]) == 1


async def test_get_course_evaluations_null_for_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id} without a session must return course_evaluations as null."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_optional_current_user] = lambda: None
    response = await client.get("/api/v1/courses/1")
    assert response.json()["course_evaluations"] is None


# ---------------------------------------------------------------------------
# POST /api/v1/courses/{course_id}/projects
# ---------------------------------------------------------------------------

_SEEDED_PROJECT = ProjectPublic(
    id=10,
    title="New Project",
    description=None,
    github_url=None,
    live_url=None,
    technologies=[],
    academic_year=2025,
    results_unlocked=False,
    course=CoursePublic(
        code="PSI",
        name="PSI Course",
        syllabus=None,
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=50,
        peer_bonus_budget=None,
        evaluation_criteria=[],
        links=[],
        lecturers=[LecturerPublic(name="Lect", github_alias=None, email="lect@tul.cz")],
    ),
    members=[],
)

_PROJECT_CREATE_PAYLOAD = {
    "title": "New Project",
    "academic_year": 2025,
}


def _make_projects_service(project: ProjectPublic | None = None) -> ProjectsService:
    """Return a mock ``ProjectsService`` configured for seeding tests."""
    service = MagicMock(spec=ProjectsService)
    service.create_project = AsyncMock(return_value=project or _SEEDED_PROJECT)
    return service


async def test_create_course_project_returns_201(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return HTTP 201 for a lecturer."""
    mock_user = _make_user(UserRole.LECTURER)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: _make_projects_service()

    response = await client.post("/api/v1/courses/1/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.status_code == 201


async def test_create_course_project_returns_201_for_admin(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return HTTP 201 for an admin."""
    mock_user = _make_user(UserRole.ADMIN)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: _make_projects_service()

    response = await client.post("/api/v1/courses/1/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.status_code == 201


async def test_create_course_project_returns_project_schema(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return the created ``ProjectPublic``."""
    mock_user = _make_user(UserRole.LECTURER)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: _make_projects_service()

    response = await client.post("/api/v1/courses/1/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.json() == _SEEDED_PROJECT.model_dump(mode="json")


async def test_create_course_project_returns_401_unauthenticated(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return HTTP 401 when not authenticated."""
    app.dependency_overrides[get_current_user] = lambda: None
    app.dependency_overrides[get_projects_service] = lambda: _make_projects_service()

    response = await client.post("/api/v1/courses/1/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.status_code == 401


async def test_create_course_project_returns_403_for_student(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return HTTP 403 when called by a student."""
    mock_user = _make_user(UserRole.STUDENT)
    mock_service = _make_projects_service()
    mock_service.create_project.side_effect = PermissionError("Not authorised.")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.post("/api/v1/courses/1/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.status_code == 403


async def test_create_course_project_returns_404_for_unknown_course(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return HTTP 404 when the course does not exist."""
    mock_user = _make_user(UserRole.ADMIN)
    mock_service = _make_projects_service()
    mock_service.create_project.side_effect = LookupError("Course 99 not found.")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.post("/api/v1/courses/99/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.status_code == 404


async def test_create_course_project_returns_500_on_service_error(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must return HTTP 500 on an unexpected error."""
    mock_user = _make_user(UserRole.ADMIN)
    mock_service = _make_projects_service()
    mock_service.create_project.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    response = await client.post("/api/v1/courses/1/projects", json=_PROJECT_CREATE_PAYLOAD)

    assert response.status_code == 500


async def test_create_course_project_forwards_data_to_service(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/projects must forward body and requester to the service."""
    mock_user = _make_user(UserRole.ADMIN)
    mock_service = _make_projects_service()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_projects_service] = lambda: mock_service

    payload = {"title": "My Project", "academic_year": 2025, "owner_email": "alice@tul.cz"}
    await client.post("/api/v1/courses/3/projects", json=payload)

    mock_service.create_project.assert_called_once()
    call_args = mock_service.create_project.call_args
    assert call_args.args[0] == 3  # course_id
    assert call_args.args[1].title == "My Project"
    assert call_args.args[1].owner_email == "alice@tul.cz"
    assert call_args.args[2] is mock_user


# POST /api/v1/courses — create course
# ---------------------------------------------------------------------------

_CREATE_BODY = {
    "code": "NEW",
    "name": "New Course",
    "term": "WINTER",
    "project_type": "TEAM",
    "min_score": 50,
}


async def test_create_course_returns_201_for_admin(client: AsyncClient) -> None:
    """POST /api/v1/courses must return HTTP 201 and the created ``CourseDetail`` for an admin."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.post("/api/v1/courses", json=_CREATE_BODY)
    assert response.status_code == 201
    assert response.json() == _COURSE_DETAIL.model_dump(mode="json")


async def test_create_course_forwards_body_to_service(client: AsyncClient) -> None:
    """POST /api/v1/courses must pass the parsed request body and current user to the service."""
    mock_user = _make_user(UserRole.ADMIN)
    mock_service = _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    await client.post("/api/v1/courses", json=_CREATE_BODY)
    mock_service.create_course.assert_called_once()
    call_args = mock_service.create_course.call_args
    assert call_args.args[1] is mock_user


async def test_create_course_returns_401_for_unauthenticated(client: AsyncClient) -> None:
    """POST /api/v1/courses must return HTTP 401 when no session is present."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: None
    response = await client.post("/api/v1/courses", json=_CREATE_BODY)
    assert response.status_code == 401


async def test_create_course_returns_403_for_lecturer(client: AsyncClient) -> None:
    """POST /api/v1/courses must return HTTP 403 when the caller is a lecturer."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.LECTURER)
    response = await client.post("/api/v1/courses", json=_CREATE_BODY)
    assert response.status_code == 403


async def test_create_course_returns_403_for_student(client: AsyncClient) -> None:
    """POST /api/v1/courses must return HTTP 403 when the caller is a student."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.STUDENT)
    response = await client.post("/api/v1/courses", json=_CREATE_BODY)
    assert response.status_code == 403


async def test_create_course_returns_409_on_duplicate_code(client: AsyncClient) -> None:
    """POST /api/v1/courses must return HTTP 409 when the course code is already in use."""
    mock_service = _make_service()
    mock_service.create_course.side_effect = IntegrityError("", {}, Exception())
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.post("/api/v1/courses", json=_CREATE_BODY)
    assert response.status_code == 409


async def test_create_course_returns_500_on_service_error(client: AsyncClient) -> None:
    """POST /api/v1/courses must return HTTP 500 when an unexpected error occurs."""
    mock_service = _make_service()
    mock_service.create_course.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.post("/api/v1/courses", json=_CREATE_BODY)
    assert response.status_code == 500


async def test_create_course_returns_422_for_missing_required_fields(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses must return HTTP 422 when required fields are missing."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.post("/api/v1/courses", json={"code": "X"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/courses/{id} — update course
# ---------------------------------------------------------------------------

_UPDATE_BODY = {"name": "Updated Name"}


async def test_update_course_returns_200_for_admin(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 200 and the updated ``CourseDetail``."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.patch("/api/v1/courses/1", json=_UPDATE_BODY)
    assert response.status_code == 200
    assert response.json() == _COURSE_DETAIL.model_dump(mode="json")


async def test_update_course_forwards_body_and_user_to_service(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must pass the course id, body, and current user to the service."""
    mock_user = _make_user(UserRole.ADMIN)
    mock_service = _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    await client.patch("/api/v1/courses/42", json=_UPDATE_BODY)
    mock_service.update_course.assert_called_once()
    call_args = mock_service.update_course.call_args
    assert call_args.args[0] == 42
    assert call_args.args[2] is mock_user


async def test_update_course_returns_401_for_unauthenticated(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 401 when no session is present."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: None
    response = await client.patch("/api/v1/courses/1", json=_UPDATE_BODY)
    assert response.status_code == 401


async def test_update_course_returns_403_on_permission_error(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 403 when the service raises permission error."""
    mock_service = _make_service()
    mock_service.update_course.side_effect = CoursePermissionError("Not allowed.")
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.STUDENT)
    response = await client.patch("/api/v1/courses/1", json=_UPDATE_BODY)
    assert response.status_code == 403


async def test_update_course_returns_404_when_not_found(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 404 when the course does not exist."""
    mock_service = _make_service(detail=None)
    mock_service.update_course = AsyncMock(return_value=None)
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.patch("/api/v1/courses/999", json=_UPDATE_BODY)
    assert response.status_code == 404


async def test_update_course_returns_409_on_duplicate_code(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 409 when the new code conflicts."""
    mock_service = _make_service()
    mock_service.update_course.side_effect = IntegrityError("", {}, Exception())
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.patch("/api/v1/courses/1", json={"code": "EXISTING"})
    assert response.status_code == 409


async def test_update_course_returns_500_on_service_error(client: AsyncClient) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 500 when an unexpected error occurs."""
    mock_service = _make_service()
    mock_service.update_course.side_effect = RuntimeError("db failure")
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.patch("/api/v1/courses/1", json=_UPDATE_BODY)
    assert response.status_code == 500


async def test_update_course_returns_422_for_null_evaluation_criteria(
    client: AsyncClient,
) -> None:
    """PATCH /api/v1/courses/{id} must return HTTP 422 when evaluation_criteria is set to null."""
    app.dependency_overrides[get_courses_service] = lambda: _make_service(detail=_COURSE_DETAIL)
    app.dependency_overrides[get_current_user] = lambda: _make_user(UserRole.ADMIN)
    response = await client.patch("/api/v1/courses/1", json={"evaluation_criteria": None})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/courses/{course_id}/lecturers — endpoint tests
# ---------------------------------------------------------------------------

_NEW_LECTURER = CourseLecturerPublic(
    id=20, name="New Lecturer", github_alias=None, email="new.lecturer@tul.cz"
)


async def test_add_course_lecturer_returns_401_when_unauthenticated(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 401 for unauthenticated requests."""
    mock_service = _make_service()
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    response = await client.post(
        "/api/v1/courses/1/lecturers", json={"email": "new.lecturer@tul.cz"}
    )
    assert response.status_code == 401


async def test_add_course_lecturer_returns_201_on_success(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 201 with the new lecturer."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.add_lecturer = AsyncMock(return_value=_NEW_LECTURER)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/courses/1/lecturers", json={"email": "new.lecturer@tul.cz"}
    )

    assert response.status_code == 201
    assert response.json() == _NEW_LECTURER.model_dump(mode="json")


async def test_add_course_lecturer_forwards_body_to_service(client: AsyncClient) -> None:
    """POST /api/v1/courses/{id}/lecturers must forward the parsed body and user to the service."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.add_lecturer = AsyncMock(return_value=_NEW_LECTURER)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    await client.post(
        "/api/v1/courses/1/lecturers",
        json={"email": "new.lecturer@tul.cz", "name": "New Lecturer"},
    )

    call_args = mock_service.add_lecturer.call_args
    assert call_args.args[0] == 1
    assert call_args.args[1].email == "new.lecturer@tul.cz"
    assert call_args.args[2] is user


async def test_add_course_lecturer_returns_404_when_course_not_found(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 404 when the course does not exist."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.add_lecturer = AsyncMock(side_effect=CourseNotFoundError("not found"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/courses/999/lecturers", json={"email": "new.lecturer@tul.cz"}
    )

    assert response.status_code == 404


async def test_add_course_lecturer_returns_403_when_not_authorised(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 403 when caller lacks write access."""
    user = _make_user(UserRole.STUDENT)
    mock_service = _make_service()
    mock_service.add_lecturer = AsyncMock(side_effect=CoursePermissionError("no access"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/courses/1/lecturers", json={"email": "new.lecturer@tul.cz"}
    )

    assert response.status_code == 403


async def test_add_course_lecturer_returns_409_when_already_assigned(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 409 when already assigned."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.add_lecturer = AsyncMock(
        side_effect=CourseLecturerAlreadyAssignedError("already assigned")
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/courses/1/lecturers", json={"email": "new.lecturer@tul.cz"}
    )

    assert response.status_code == 409


async def test_add_course_lecturer_returns_422_for_non_tul_email(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 422 for non-@tul.cz addresses."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/courses/1/lecturers", json={"email": "lecturer@gmail.com"}
    )

    assert response.status_code == 422


async def test_add_course_lecturer_returns_500_on_service_error(
    client: AsyncClient,
) -> None:
    """POST /api/v1/courses/{id}/lecturers must return HTTP 500 on unexpected service error."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.add_lecturer = AsyncMock(side_effect=RuntimeError("db failure"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/courses/1/lecturers", json={"email": "new.lecturer@tul.cz"}
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/v1/courses/{course_id}/lecturers/{user_id} — endpoint tests
# ---------------------------------------------------------------------------


async def test_remove_course_lecturer_returns_401_when_unauthenticated(
    client: AsyncClient,
) -> None:
    """DELETE /api/v1/courses/{id}/lecturers/{user_id} must return HTTP 401 when unauthenticated."""
    mock_service = _make_service()
    app.dependency_overrides[get_courses_service] = lambda: mock_service
    response = await client.delete("/api/v1/courses/1/lecturers/20")
    assert response.status_code == 401


async def test_remove_course_lecturer_returns_204_on_success(client: AsyncClient) -> None:
    """DELETE /api/v1/courses/{id}/lecturers/{user_id} must return HTTP 204 on success."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.remove_lecturer = AsyncMock(return_value=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.delete("/api/v1/courses/1/lecturers/20")

    assert response.status_code == 204


async def test_remove_course_lecturer_returns_403_when_not_authorised(
    client: AsyncClient,
) -> None:
    """DELETE /api/v1/courses/{id}/lecturers/{user_id} must return HTTP 403 when lacking access."""
    user = _make_user(UserRole.STUDENT)
    mock_service = _make_service()
    mock_service.remove_lecturer = AsyncMock(side_effect=CoursePermissionError("no access"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.delete("/api/v1/courses/1/lecturers/20")

    assert response.status_code == 403


async def test_remove_course_lecturer_returns_404_when_not_assigned(
    client: AsyncClient,
) -> None:
    """DELETE /api/v1/courses/{id}/lecturers/{user_id} must return HTTP 404 when not assigned."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.remove_lecturer = AsyncMock(
        side_effect=CourseLecturerNotAssignedError("not assigned")
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.delete("/api/v1/courses/1/lecturers/999")

    assert response.status_code == 404


async def test_remove_course_lecturer_returns_404_when_course_not_found(
    client: AsyncClient,
) -> None:
    """DELETE /api/v1/courses/{id}/lecturers/{user_id} must return HTTP 404 when course missing."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.remove_lecturer = AsyncMock(side_effect=CourseNotFoundError("not found"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.delete("/api/v1/courses/999/lecturers/20")

    assert response.status_code == 404


async def test_remove_course_lecturer_returns_500_on_service_error(
    client: AsyncClient,
) -> None:
    """DELETE /api/v1/courses/{id}/lecturers/{user_id} must return HTTP 500 on unexpected error."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.remove_lecturer = AsyncMock(side_effect=RuntimeError("db failure"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.delete("/api/v1/courses/1/lecturers/20")

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/v1/courses/{course_id}/evaluation-overview
# ---------------------------------------------------------------------------

_OVERVIEW = EvaluationOverviewResponse(
    projects=[
        ProjectOverviewItem(
            project_id=1,
            project_title="Project Alpha",
            academic_year=2025,
            project_evaluations=[
                ProjectEvaluationSummary(
                    lecturer_id=10,
                    criterion_scores=[
                        CriterionScoreSummary(
                            criterion_code="code_quality",
                            score=18,
                            strengths="Good code.",
                            improvements="More tests.",
                        )
                    ],
                )
            ],
            course_evaluations=[
                CourseEvaluationSummary(rating=4, strengths="Great.", improvements=None)
            ],
            student_bonus_points=[
                StudentBonusSummary(
                    student_id=5,
                    student_name="Alice",
                    feedback=[
                        ReceivedPeerFeedback(bonus_points=3, strengths=None, improvements=None)
                    ],
                )
            ],
        )
    ]
)


def _make_courses_service_with_overview(
    overview: EvaluationOverviewResponse | None = None,
) -> CoursesService:
    """Return a mock ``CoursesService`` with ``get_evaluation_overview`` pre-configured."""
    service = _make_service()
    service.get_evaluation_overview = AsyncMock(return_value=overview or _OVERVIEW)
    return service


async def test_get_evaluation_overview_returns_200(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must return HTTP 200 for an authorised user."""
    user = _make_user(UserRole.LECTURER)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: _make_courses_service_with_overview()

    response = await client.get("/api/v1/courses/1/evaluation-overview")

    assert response.status_code == 200


async def test_get_evaluation_overview_returns_schema(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must return the full overview schema."""
    user = _make_user(UserRole.ADMIN)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: _make_courses_service_with_overview()

    response = await client.get("/api/v1/courses/1/evaluation-overview")

    assert response.json() == _OVERVIEW.model_dump(mode="json")


async def test_get_evaluation_overview_returns_401_when_unauthenticated(
    client: AsyncClient,
) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must return HTTP 401 when not authenticated."""
    app.dependency_overrides[get_current_user] = lambda: None
    app.dependency_overrides[get_courses_service] = lambda: _make_courses_service_with_overview()

    response = await client.get("/api/v1/courses/1/evaluation-overview")

    assert response.status_code == 401


async def test_get_evaluation_overview_returns_403_on_permission_error(
    client: AsyncClient,
) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must return HTTP 403 when access is denied."""
    user = _make_user(UserRole.STUDENT)
    mock_service = _make_service()
    mock_service.get_evaluation_overview = AsyncMock(
        side_effect=CoursePermissionError("Not authorised.")
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.get("/api/v1/courses/1/evaluation-overview")

    assert response.status_code == 403


async def test_get_evaluation_overview_returns_404_when_course_not_found(
    client: AsyncClient,
) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must return HTTP 404 when course is missing."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.get_evaluation_overview = AsyncMock(
        side_effect=CourseNotFoundError("Course 99 not found.")
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.get("/api/v1/courses/99/evaluation-overview")

    assert response.status_code == 404


async def test_get_evaluation_overview_forwards_year_filter(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must forward the year query parameter."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_courses_service_with_overview()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    await client.get("/api/v1/courses/5/evaluation-overview?year=2025")

    mock_service.get_evaluation_overview.assert_called_once_with(5, year=2025, requester=user)


async def test_get_evaluation_overview_forwards_none_when_no_year(client: AsyncClient) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must pass year=None when omitted."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_courses_service_with_overview()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    await client.get("/api/v1/courses/5/evaluation-overview")

    mock_service.get_evaluation_overview.assert_called_once_with(5, year=None, requester=user)


async def test_get_evaluation_overview_returns_500_on_unexpected_error(
    client: AsyncClient,
) -> None:
    """GET /api/v1/courses/{id}/evaluation-overview must return HTTP 500 on unexpected error."""
    user = _make_user(UserRole.ADMIN)
    mock_service = _make_service()
    mock_service.get_evaluation_overview = AsyncMock(side_effect=RuntimeError("db failure"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_courses_service] = lambda: mock_service

    response = await client.get("/api/v1/courses/1/evaluation-overview")

    assert response.status_code == 500
