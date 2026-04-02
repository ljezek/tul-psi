from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.session import get_session
from models.user import User
from schemas.courses import CourseDetail, CourseListItem
from services.courses import CoursesService

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
    current_user: User | None = Depends(get_current_user),
) -> list[CourseListItem]:
    """Return all courses with aggregated stats.

    Each item includes the course code, name, syllabus, sorted lecturer names,
    and a ``stats`` object with the total project count and distinct academic years.
    """
    try:
        return await service.get_courses(current_user=current_user)
    except Exception:
        logger.exception("Failed to retrieve courses")
        raise HTTPException(status_code=500, detail="Internal server error.") from None


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
    current_user: User | None = Depends(get_current_user),
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
