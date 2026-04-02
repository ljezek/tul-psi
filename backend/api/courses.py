from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_optional_current_user, require_current_user
from db.session import get_session
from models.user import User, UserRole
from schemas.courses import CourseCreate, CourseDetail, CourseListItem, CourseUpdate
from services.courses import CoursePermissionError, CoursesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


def get_courses_service(session: AsyncSession = Depends(get_session)) -> CoursesService:
    """Provide a ``CoursesService`` instance wired to the current DB session."""
    return CoursesService(session)


@router.get(
    "",
    response_model=list[CourseListItem],
    summary="List courses",
    description=(
        "Returns all courses with their codes, names, syllabus, lecturer names, "
        "and aggregated project stats.  No authentication is required."
    ),
)
async def list_courses(
    service: CoursesService = Depends(get_courses_service),
) -> list[CourseListItem]:
    """Return all courses with aggregated stats.

    Each item includes the course code, name, syllabus, sorted lecturer names,
    and a ``stats`` object with the total project count and distinct academic years.
    Authentication is not required.
    """
    try:
        return await service.get_courses()
    except Exception:
        logger.exception("Failed to retrieve courses")
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.post(
    "",
    response_model=CourseDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a course",
    description=(
        "Creates a new course.  "
        "Requires an authenticated admin session.  "
        "Returns HTTP 401 when unauthenticated, HTTP 403 when authenticated but not an admin, "
        "and HTTP 409 when a course with the same code already exists."
    ),
)
async def create_course(
    body: CourseCreate,
    service: CoursesService = Depends(get_courses_service),
    current_user: User = Depends(require_current_user),
) -> CourseDetail:
    """Create and return a new course.

    Only admins may call this endpoint.  Raises HTTP 401 when the request is
    unauthenticated and HTTP 403 when the caller is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create courses.",
        )
    try:
        return await service.create_course(body, current_user)
    except IntegrityError:
        logger.warning("Course creation failed: duplicate code.", extra={"code": body.code})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A course with code '{body.code}' already exists.",
        ) from None
    except Exception:
        logger.exception("Failed to create course", extra={"code": body.code})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.patch(
    "/{course_id}",
    response_model=CourseDetail,
    summary="Update a course",
    description=(
        "Partially updates an existing course.  "
        "Only fields included in the request body are changed; omitted fields keep their "
        "current values.  "
        "Requires an authenticated admin or lecturer session; lecturers must be assigned "
        "to the course.  "
        "Returns HTTP 401 when unauthenticated, HTTP 403 when the caller lacks permission, "
        "HTTP 404 when the course does not exist, and HTTP 409 when the new code conflicts "
        "with an existing course."
    ),
)
async def update_course(
    course_id: int,
    body: CourseUpdate,
    service: CoursesService = Depends(get_courses_service),
    current_user: User = Depends(require_current_user),
) -> CourseDetail:
    """Partially update the course identified by ``course_id``.

    Raises HTTP 401 when the request is unauthenticated, HTTP 403 when the
    caller is a student or a lecturer not assigned to this course, and HTTP
    404 when no course with the given id exists.
    """
    try:
        result = await service.update_course(course_id, body, current_user)
    except CoursePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except IntegrityError:
        logger.warning(
            "Course update failed: duplicate code.",
            extra={"course_id": course_id, "code": body.code},
        )
        detail = (
            f"A course with code '{body.code}' already exists."
            if body.code is not None
            else "A unique constraint was violated."
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        ) from None
    except Exception:
        logger.exception("Failed to update course", extra={"course_id": course_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None

    if result is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")
    return result


@router.get(
    "/{course_id}",
    response_model=CourseDetail,
    summary="Get course detail",
    description=(
        "Returns the full public detail of a single course identified by its integer id. "
        "Authenticated admins and assigned lecturers additionally receive the "
        "``course_evaluations`` field.  No authentication is required for the base response."
    ),
)
async def get_course(
    course_id: int,
    service: CoursesService = Depends(get_courses_service),
    current_user: User | None = Depends(get_optional_current_user),
) -> CourseDetail:
    """Return the course identified by ``course_id``.

    Raises HTTP 404 when no course with the given id exists.
    """
    try:
        course = await service.get_course(course_id, current_user=current_user)
    except Exception:
        logger.exception("Failed to retrieve course", extra={"course_id": course_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None

    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")
    return course
