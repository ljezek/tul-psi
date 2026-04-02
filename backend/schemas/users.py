from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from models.user import UserRole


class UserPublic(BaseModel):
    """Schema for public user representation."""

    id: int
    email: EmailStr
    github_alias: str | None = None
    name: str
    role: UserRole
    is_active: bool


class UserCreate(BaseModel):
    """Schema for admins to create a new user."""

    email: EmailStr
    name: str = Field(max_length=255)
    github_alias: str | None = Field(default=None, max_length=100)
    role: UserRole = UserRole.STUDENT
    is_active: bool = True


class UserUpdate(BaseModel):
    """Schema for updating a user's own profile."""

    name: str | None = Field(default=None, max_length=255)
    github_alias: str | None = Field(default=None, max_length=100)


class AdminUserUpdate(UserUpdate):
    """Schema for admins to update any user, including their role."""

    role: UserRole | None = None
    is_active: bool | None = None
