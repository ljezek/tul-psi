from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_optional_current_user, require_current_user
from db.session import get_session
from models.user import User, UserRole
from schemas.courses import (
    CourseCreate,
    CourseDetail,
    CourseLecturerPublic,
    CourseListItem,
    CourseUpdate,
)
from schemas.projects import AddUserBody, ProjectCreate, ProjectPublic
from services.courses import (
    CourseLecturerAlreadyAssignedError,
    CourseLecturerNotAssignedError,
    CourseNotFoundError,
    CoursePermissionError,
    CoursesService,
)
from services.projects import ProjectsService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


def get_courses_service(session: AsyncSession = Depends(get_session)) -> CoursesService:
    """Provide a ``CoursesService`` instance wired to the current DB session."""
    return CoursesService(session)


def get_projects_service(session: AsyncSession = Depends(get_session)) -> ProjectsService:
    """Provide a ``ProjectsService`` instance wired to the current DB session."""
    return ProjectsService(session)


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


@router.post(
    "/{course_id}/projects",
    response_model=ProjectPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Seed a project",
    description=(
        "Creates a new project for the specified course. "
        "Only accessible to admin users or lecturers assigned to the course. "
        "When ``owner_email`` is provided, the system looks up (or creates) the student "
        "account, seeds an initial project member, and simulates sending an invite email."
    ),
)
async def create_course_project(
    course_id: int,
    data: ProjectCreate,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectPublic:
    """Create a new project for the course identified by ``course_id``.

    Raises HTTP 401 when the caller is not authenticated.
    Raises HTTP 403 when the caller is not an admin or assigned lecturer.
    Raises HTTP 404 when the course does not exist.
    """
    try:
        return await service.create_project(course_id, data, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found.",
        ) from None
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to manage projects for this course.",
        ) from None
    except Exception:
        logger.exception(
            "Failed to create project",
            extra={"course_id": course_id},
        )      
      

@router.post(
    "/{course_id}/lecturers",
    response_model=CourseLecturerPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a lecturer to a course",
    description=(
        "Assigns a lecturer to the course by e-mail address.  "
        "Creates a new LECTURER account if no user with that address exists.  "
        "A notification with a login link is logged for the invited user "
        "(e-mail delivery is not yet implemented).  "
        "Requires authentication as an ADMIN or a lecturer already assigned to this course."
    ),
)
async def add_course_lecturer(
    course_id: int,
    body: AddUserBody,
    current_user: User = Depends(require_current_user),
    service: CoursesService = Depends(get_courses_service),
) -> CourseLecturerPublic:
    """Assign the user identified by ``body.email`` as a lecturer on the course.

    Raises HTTP 401 when unauthenticated, HTTP 403 when the caller lacks write
    access, HTTP 404 when the course does not exist, and HTTP 409 when the
    target user is already a lecturer on this course.
    """
    try:
        result = await service.add_lecturer(course_id, body, current_user)
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found.",
        ) from None
    except CoursePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CourseLecturerAlreadyAssignedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception:
        logger.exception("Failed to add course lecturer", extra={"course_id": course_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None

    return result


@router.delete(
    "/{course_id}/lecturers/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Unassign a lecturer from a course",
    description=(
        "Removes the lecturer assignment for the given user from the course.  "
        "The user account is not deleted from the system.  "
        "Requires authentication as an ADMIN or a lecturer already assigned to this course."
    ),
)
async def remove_course_lecturer(
    course_id: int,
    user_id: int,
    current_user: User = Depends(require_current_user),
    service: CoursesService = Depends(get_courses_service),
) -> None:
    """Remove the lecturer assignment for ``user_id`` from the course.

    Raises HTTP 401 when unauthenticated, HTTP 403 when the caller lacks write
    access, HTTP 404 when the course or the assignment does not exist.
    """
    try:
        await service.remove_lecturer(course_id, user_id, current_user)
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found.",
        ) from None
    except CoursePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CourseLecturerNotAssignedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not a lecturer on course {course_id}.",
        ) from None
    except Exception:
        logger.exception("Failed to remove course lecturer", extra={"course_id": course_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None
