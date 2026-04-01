from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from models.course import CourseTerm
from schemas.projects import ProjectPublic
from services.projects import ProjectsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


def get_projects_service(session: AsyncSession = Depends(get_session)) -> ProjectsService:
    """Provide a ``ProjectsService`` instance wired to the current DB session."""
    return ProjectsService(session)


@router.get(
    "",
    response_model=list[ProjectPublic],
    summary="List projects",
    description=(
        "Returns all projects visible to unauthenticated users. "
        "Results can be narrowed with any combination of the optional "
        "query parameters."
    ),
)
async def list_projects(
    q: str | None = None,
    course: str | None = None,
    year: int | None = None,
    term: CourseTerm | None = None,
    lecturer: str | None = None,
    technology: str | None = None,
    service: ProjectsService = Depends(get_projects_service),
) -> list[ProjectPublic]:
    """Return projects filtered by the supplied query parameters.

    All parameters are optional; omitting a parameter disables that filter.

    - **q**: full-text search on project title and description (case-insensitive).
    - **course**: exact match on course code (e.g. ``PSI``).
    - **year**: filter by academic year (e.g. ``2025``).
    - **term**: filter by course term — ``WINTER`` or ``SUMMER``.
    - **lecturer**: partial match on the lecturer's name or e-mail address.
    - **technology**: exact match on a technology name in the project's technologies list.
    """
    try:
        return await service.get_projects(
            q=q,
            course=course,
            year=year,
            term=term,
            lecturer=lecturer,
            technology=technology,
        )
    except Exception:
        logger.exception(
            "Failed to retrieve projects",
            extra={
                "q": q,
                "course": course,
                "year": year,
                "term": term,
                "lecturer": lecturer,
                "technology": technology,
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error.") from None
