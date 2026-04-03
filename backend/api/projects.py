from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_optional_current_user, require_current_user
from db.session import get_session
from models.course import CourseTerm
from models.user import User
from schemas.projects import (
    AddMemberBody,
    MemberPublic,
    ProjectEvaluationCreate,
    ProjectEvaluationDetail,
    ProjectPublic,
    ProjectUpdate,
)
from services.projects import (
    AlreadyMemberError,
    EvaluationConflictError,
    InvalidEvaluationDataError,
    PermissionDeniedError,
    ProjectNotFoundError,
    ProjectsService,
)

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


@router.get(
    "/{project_id}",
    response_model=ProjectPublic,
    summary="Get project detail",
    description=(
        "Returns the full detail of a single project identified by its integer id. "
        "Authenticated requests (valid ``session`` cookie) receive an enriched response "
        "that includes member and lecturer e-mails, the ``results_unlocked`` flag, and — "
        "when results are unlocked — role-appropriate evaluation data."
    ),
)
async def get_project(
    project_id: int,
    current_user: User | None = Depends(get_optional_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectPublic:
    """Return the project identified by ``project_id``.

    Unauthenticated callers receive a ``ProjectPublic`` response with private fields
    (e-mails, evaluations, ``results_unlocked``) set to ``None``.  Authenticated
    callers receive the same schema with those fields populated according to their role.

    Raises HTTP 404 when no project with the given id exists.
    """
    try:
        if current_user is not None:
            project = await service.get_project_detail(project_id, current_user)
        else:
            project = await service.get_project(project_id)
    except Exception:
        logger.exception("Failed to retrieve project", extra={"project_id": project_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectPublic,
    summary="Update project",
    description=(
        "Updates the editable fields of an existing project. "
        "Only the fields included in the request body are modified; "
        "omitted fields are left unchanged. "
        "Requires authentication as an ADMIN, a project member (STUDENT), "
        "or a lecturer on the project's course."
    ),
)
async def patch_project(
    project_id: int,
    body: ProjectUpdate,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectPublic:
    """Apply partial updates to the project identified by *project_id*.

    Only the non-``None`` fields in the request body are written. Raises HTTP 401
    when unauthenticated, HTTP 403 when the caller is not a project member or
    course lecturer, and HTTP 404 when the project does not exist.
    """
    try:
        return await service.patch_project(project_id, body, current_user)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        ) from None
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to modify project {project_id}.",
        ) from None
    except Exception:
        logger.exception(
            "Failed to update project",
            extra={"project_id": project_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.post(
    "/{project_id}/members",
    response_model=MemberPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add project member",
    description=(
        "Adds a member to the project by e-mail address. "
        "Creates a new STUDENT account if no user with that address exists. "
        "A notification with a login link is logged for the invited user "
        "(e-mail delivery is not yet implemented). "
        "Requires authentication as a project member (STUDENT) "
        "or a lecturer on the project's course."
    ),
)
async def add_project_member(
    project_id: int,
    body: AddMemberBody,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> MemberPublic:
    """Add the user identified by ``body.email`` to the project.

    Raises HTTP 401 when unauthenticated, HTTP 403 when the caller lacks write
    access, HTTP 404 when the project does not exist, and HTTP 409 when the
    target user is already a member.
    """
    try:
        return await service.add_member(project_id, body, current_user)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        ) from None
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to modify project {project_id}.",
        ) from None
    except AlreadyMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user is already a member of the project.",
        ) from None
    except Exception:
        logger.exception(
            "Failed to add project member",
            extra={"project_id": project_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.post(
    "/{project_id}/unlock",
    response_model=ProjectPublic,
    summary="Unlock project results",
    description=(
        "Manually unlocks the evaluation results for the specified project, "
        "overriding the automatic unlock condition. "
        "Only accessible to admin users or lecturers assigned to the project's course."
    ),
)
async def unlock_project(
    project_id: int,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectPublic:
    """Set ``results_unlocked=True`` on the project identified by ``project_id``.

    Raises HTTP 401 when the caller is not authenticated.
    Raises HTTP 403 when the caller is not an admin or assigned lecturer.
    Raises HTTP 404 when the project does not exist.
    """
    try:
        return await service.unlock_project(project_id, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        ) from None
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to unlock results for this project.",
        ) from None
    except Exception:
        logger.exception("Failed to unlock project results", extra={"project_id": project_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.get(
    "/{project_id}/project-evaluation",
    response_model=ProjectEvaluationDetail,
    summary="Get project evaluation",
    description=(
        "Returns the calling lecturer's evaluation (draft or submitted) for the specified project. "
        "Returns HTTP 404 when no evaluation row exists for the lecturer. "
        "Only accessible to admin users or lecturers assigned to the project's course."
    ),
)
async def get_project_evaluation(
    project_id: int,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectEvaluationDetail:
    """Return the evaluation row for the calling lecturer for ``project_id``.

    Raises HTTP 401 when the caller is not authenticated.
    Raises HTTP 403 when the caller is not an admin or assigned lecturer.
    Raises HTTP 404 when the project does not exist or no evaluation row exists
    for this lecturer.
    """
    try:
        return await service.get_project_evaluation(project_id, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evaluation found for project {project_id}.",
        ) from None
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to access evaluation for this project.",
        ) from None
    except Exception:
        logger.exception("Failed to retrieve project evaluation", extra={"project_id": project_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.post(
    "/{project_id}/project-evaluation",
    response_model=ProjectEvaluationDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Submit project evaluation",
    description=(
        "Creates or updates the calling lecturer's evaluation for the specified project. "
        "Set ``submitted=False`` (default) to save a draft that can be updated later. "
        "Set ``submitted=True`` to finalise the evaluation; once all lecturers have submitted "
        "and all students have submitted their course evaluations, the project results are "
        "unlocked automatically and notification emails are sent to all participants. "
        "Editing is blocked (HTTP 409) once the project results have been unlocked. "
        "Only accessible to users explicitly assigned as lecturers for the project's course. "
        "Admin users who are not assigned as course lecturers are denied (HTTP 403)."
    ),
)
async def save_project_evaluation(
    project_id: int,
    body: ProjectEvaluationCreate,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectEvaluationDetail:
    """Create or update the calling lecturer's evaluation for ``project_id``.

    Raises HTTP 401 when the caller is not authenticated.
    Raises HTTP 403 when the caller is not an assigned lecturer for the project's course
    (admin users without a lecturer assignment are also denied).
    Raises HTTP 404 when the project does not exist.
    Raises HTTP 409 when the project results are already unlocked.
    Raises HTTP 422 when a criterion code is not configured for the course or
    a score value is outside the allowed range.
    """
    try:
        return await service.save_project_evaluation(project_id, body, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        ) from None
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to submit evaluation for this project.",
        ) from None
    except EvaluationConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project results are already unlocked; evaluation cannot be edited.",
        ) from None
    except InvalidEvaluationDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except Exception:
        logger.exception("Failed to submit project evaluation", extra={"project_id": project_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description=(
        "Deletes the specified project and all its associated data. "
        "Only accessible to admin users or lecturers assigned to the project's course."
    ),
)
async def delete_project(
    project_id: int,
    current_user: User = Depends(require_current_user),
    service: ProjectsService = Depends(get_projects_service),
) -> Response:
    """Delete the project identified by ``project_id``.

    Raises HTTP 401 when the caller is not authenticated.
    Raises HTTP 403 when the caller is not an admin or assigned lecturer.
    Raises HTTP 404 when the project does not exist.
    """
    try:
        await service.delete_project(project_id, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        ) from None
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to delete this project.",
        ) from None
    except Exception:
        logger.exception("Failed to delete project", extra={"project_id": project_id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
