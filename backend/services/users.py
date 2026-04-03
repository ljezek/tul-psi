from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from db.users import get_or_create_user as db_get_or_create_user
from db.users import get_user as db_get_user
from db.users import get_users as db_get_users
from models.user import User, UserRole
from schemas.users import AdminUserUpdate, UserCreate, UserPublic, UserUpdate
from validators import require_user_id

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when a user with the requested ID does not exist."""


class UserAlreadyExistsError(Exception):
    """Raised when an admin attempts to create a user that already exists."""


class PermissionDeniedError(Exception):
    """Raised when a user attempts an operation without sufficient permissions."""


class UsersService:
    """Business logic for user management endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_users(self, current_user: User) -> list[UserPublic]:
        """Return all users. Restricted to ADMIN users."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can list users.")

        users = await db_get_users(self._session)
        return [
            UserPublic(
                id=require_user_id(u),
                email=u.email,
                github_alias=u.github_alias,
                name=u.name,
                role=u.role,
                is_active=u.is_active,
            )
            for u in users
        ]

    async def get_user(self, user_id: int, current_user: User) -> UserPublic:
        """Return the user identified by *user_id*. Restricted to ADMIN users."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can view other users.")

        user = await db_get_user(self._session, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found.")

        return UserPublic(
            id=require_user_id(user),
            email=user.email,
            github_alias=user.github_alias,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
        )

    async def update_user(
        self,
        user_id: int,
        body: AdminUserUpdate,
        current_user: User,
    ) -> UserPublic:
        """Update any user. Restricted to ADMIN users."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can update other users.")

        user = await db_get_user(self._session, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found.")

        if body.name is not None:
            user.name = body.name
        if body.github_alias is not None:
            user.github_alias = body.github_alias
        if body.role is not None:
            user.role = body.role
        if body.is_active is not None:
            user.is_active = body.is_active

        await self._session.commit()
        return UserPublic(
            id=require_user_id(user),
            email=user.email,
            github_alias=user.github_alias,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
        )

    async def update_me(self, body: UserUpdate, current_user: User) -> UserPublic:
        """Update the current user's own profile."""
        if body.name is not None:
            current_user.name = body.name
        if body.github_alias is not None:
            current_user.github_alias = body.github_alias

        await self._session.commit()
        return UserPublic(
            id=require_user_id(current_user),
            email=current_user.email,
            github_alias=current_user.github_alias,
            name=current_user.name,
            role=current_user.role,
            is_active=current_user.is_active,
        )

    async def create_user(self, body: UserCreate, current_user: User) -> UserPublic:
        """Create a new user. Restricted to ADMIN users."""
        if current_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can create users.")

        user, created = await db_get_or_create_user(
            self._session,
            email=body.email,
            name=body.name,
            github_alias=body.github_alias,
            role=body.role,
        )

        if not created:
            raise UserAlreadyExistsError(f"User with email {body.email} already exists.")

        user.is_active = body.is_active

        await self._session.commit()
        return UserPublic(
            id=require_user_id(user),
            email=user.email,
            github_alias=user.github_alias,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
        )
