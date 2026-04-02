from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_current_user
from db.session import get_session
from models.user import User
from schemas.users import AdminUserUpdate, UserCreate, UserPublic, UserUpdate
from services.users import (
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UsersService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_users_service(session: AsyncSession = Depends(get_session)) -> UsersService:
    """Provide a ``UsersService`` instance wired to the current DB session."""
    return UsersService(session)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user's profile",
    description="Returns the profile details of the currently authenticated user.",
)
async def get_me(current_user: User = Depends(require_current_user)) -> UserPublic:
    """Return the currently authenticated user."""
    return UserPublic(
        id=current_user.id,  # type: ignore
        email=current_user.email,
        github_alias=current_user.github_alias,
        name=current_user.name,
        role=current_user.role,
    )


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update current user's profile",
    description="Updates the name or GitHub alias of the currently authenticated user.",
)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(require_current_user),
    service: UsersService = Depends(get_users_service),
) -> UserPublic:
    """Partially update the current user's profile."""
    try:
        return await service.update_me(body, current_user)
    except Exception:
        logger.exception("Failed to update user profile", extra={"user_id": current_user.id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.post(
    "",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user account. Restricted to ADMIN users.",
)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_current_user),
    service: UsersService = Depends(get_users_service),
) -> UserPublic:
    """Create a new user. Only admins can create users."""
    try:
        return await service.create_user(body, current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception:
        logger.exception("Failed to create user", extra={"caller_id": current_user.id, "email": body.email})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.get(
    "",
    response_model=list[UserPublic],
    summary="List users",
    description="Returns all users in the system. Restricted to ADMIN users.",
)
async def list_users(
    current_user: User = Depends(require_current_user),
    service: UsersService = Depends(get_users_service),
) -> list[UserPublic]:
    """Return all users. Only admins can list users."""
    try:
        return await service.get_users(current_user)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception:
        logger.exception("Failed to list users", extra={"user_id": current_user.id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Get user by ID",
    description="Returns the profile details of a user identified by its integer ID. Restricted to ADMIN users.",
)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_current_user),
    service: UsersService = Depends(get_users_service),
) -> UserPublic:
    """Return the user identified by *user_id*. Only admins can view other users."""
    try:
        return await service.get_user(user_id, current_user)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception:
        logger.exception("Failed to retrieve user", extra={"user_id": user_id, "caller_id": current_user.id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None


@router.patch(
    "/{user_id}",
    response_model=UserPublic,
    summary="Update user by ID",
    description="Updates the profile details of a user identified by its integer ID. Restricted to ADMIN users.",
)
async def update_user_by_id(
    user_id: int,
    body: AdminUserUpdate,
    current_user: User = Depends(require_current_user),
    service: UsersService = Depends(get_users_service),
) -> UserPublic:
    """Update the user identified by *user_id*. Only admins can update other users."""
    try:
        return await service.update_user(user_id, body, current_user)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception:
        logger.exception("Failed to update user", extra={"user_id": user_id, "caller_id": current_user.id})
        raise HTTPException(status_code=500, detail="Internal server error.") from None
