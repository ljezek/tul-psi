from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
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
        "Returns all courses with their codes, names, and aggregated stats "
        "(project count, academic years, and lecturer names). "
        "No authentication is required."
    ),
)
async def list_courses(
    service: CoursesService = Depends(get_courses_service),
) -> list[CourseListItem]:
    """Return all courses with aggregated stats.

    Each item includes the course code and name together with a ``stats``
    object containing the total project count, the list of distinct academic
    years, and the list of lecturer names.
    """
    try:
        return await service.get_courses()
    except Exception:
        logger.exception("Failed to retrieve courses")
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.get(
    "/{course_id}",
    response_model=CourseDetail,
    summary="Get course detail",
    description=(
        "Returns the full public detail of a single course identified by its integer id. "
        "No authentication is required."
    ),
)
async def get_course(
    course_id: int,
    service: CoursesService = Depends(get_courses_service),
) -> CourseDetail:
    """Return the course identified by ``course_id``.

    Raises HTTP 404 when no course with the given id exists.
    """
    try:
        course = await service.get_course(course_id)
    except Exception:
        logger.exception("Failed to retrieve course", extra={"course_id": course_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None

    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")
    return course
