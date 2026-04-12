from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.user import User, UserRole
from schemas.users import AdminUserUpdate, UserCreate, UserUpdate
from services.users import (
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UsersService,
)


def _make_user(user_id: int = 1, role: UserRole = UserRole.STUDENT) -> User:
    """Return a mock User model with the given id and role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"user{user_id}@tul.cz"
    user.name = f"User {user_id}"
    user.role = role
    user.is_active = True
    user.github_alias = None
    return user


@pytest.mark.asyncio
async def test_get_users_as_admin() -> None:
    """get_users must return all users for an admin."""
    admin = _make_user(role=UserRole.ADMIN)
    users = [_make_user(1), _make_user(2)]
    session = MagicMock()

    with patch("services.users.db_get_users", new_callable=AsyncMock, return_value=users):
        result = await UsersService(session).get_users(admin)

    assert len(result) == 2
    assert result[0].email == "user1@tul.cz"
    assert result[1].email == "user2@tul.cz"


@pytest.mark.asyncio
async def test_get_users_as_student_raises_error() -> None:
    """get_users must raise PermissionDeniedError for non-admins."""
    student = _make_user(role=UserRole.STUDENT)
    session = MagicMock()

    with pytest.raises(PermissionDeniedError):
        await UsersService(session).get_users(student)


@pytest.mark.asyncio
async def test_get_user_by_id_as_admin() -> None:
    """get_user must return the requested user for an admin."""
    admin = _make_user(role=UserRole.ADMIN)
    target_user = _make_user(user_id=5)
    session = MagicMock()

    with patch("services.users.db_get_user", new_callable=AsyncMock, return_value=target_user):
        result = await UsersService(session).get_user(5, admin)

    assert result.id == 5
    assert result.email == "user5@tul.cz"


@pytest.mark.asyncio
async def test_get_user_not_found_raises_error() -> None:
    """get_user must raise UserNotFoundError when the user does not exist."""
    admin = _make_user(role=UserRole.ADMIN)
    session = MagicMock()

    with patch("services.users.db_get_user", new_callable=AsyncMock, return_value=None):
        with pytest.raises(UserNotFoundError):
            await UsersService(session).get_user(999, admin)


@pytest.mark.asyncio
async def test_update_me_updates_profile() -> None:
    """update_me must update the current user's own profile and commit."""
    user = _make_user()
    session = MagicMock()
    session.commit = AsyncMock()
    body = UserUpdate(name="New Name", github_alias="newalias")

    result = await UsersService(session).update_me(body, user)

    assert user.name == "New Name"
    assert user.github_alias == "newalias"
    session.commit.assert_called_once()
    assert result.name == "New Name"


@pytest.mark.asyncio
async def test_update_user_as_admin() -> None:
    """update_user must allow admins to update any user's role and status."""
    admin = _make_user(role=UserRole.ADMIN)
    target_user = _make_user(user_id=10, role=UserRole.STUDENT)
    session = MagicMock()
    session.commit = AsyncMock()
    body = AdminUserUpdate(role=UserRole.LECTURER, is_active=False)

    with patch("services.users.db_get_user", new_callable=AsyncMock, return_value=target_user):
        result = await UsersService(session).update_user(10, body, admin)

    assert target_user.role == UserRole.LECTURER
    assert target_user.is_active is False
    session.commit.assert_called_once()
    assert result.role == UserRole.LECTURER


@pytest.mark.asyncio
async def test_create_user_as_admin_sends_invite() -> None:
    """create_user must create a user and send an invitation email."""
    admin = _make_user(role=UserRole.ADMIN)
    new_user = _make_user(user_id=3)
    session = MagicMock()
    session.commit = AsyncMock()
    body = UserCreate(email="new@tul.cz", name="New User", role=UserRole.LECTURER, is_active=True)

    with (
        patch(
            "services.users.db_get_or_create_user",
            new_callable=AsyncMock,
            return_value=(new_user, True),
        ),
        patch("services.users.EmailSender") as mock_email_sender_class,
        patch("services.users.get_settings") as mock_get_settings,
    ):
        mock_get_settings.return_value = MagicMock(frontend_url="http://portal.test")
        mock_sender_instance = mock_email_sender_class.return_value

        result = await UsersService(session).create_user(body, admin)

    assert result.email == "user3@tul.cz"
    session.commit.assert_called_once()

    # Verify email was "sent"
    mock_email_sender_class.assert_called_once()
    mock_sender_instance.send.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_already_exists_raises_error() -> None:
    """create_user must raise UserAlreadyExistsError if the email is taken."""
    admin = _make_user(role=UserRole.ADMIN)
    existing_user = _make_user()
    session = MagicMock()
    body = UserCreate(email="exists@tul.cz", role=UserRole.STUDENT)

    with patch(
        "services.users.db_get_or_create_user",
        new_callable=AsyncMock,
        return_value=(existing_user, False),
    ):
        with pytest.raises(UserAlreadyExistsError):
            await UsersService(session).create_user(body, admin)
