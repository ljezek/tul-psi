from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_current_user
from db.session import get_session
from main import app
from models.user import User, UserRole


@pytest.fixture
def mock_user() -> User:
    user = User(
        id=1,
        email="test@tul.cz",
        name="Test User",
        role=UserRole.STUDENT,
        github_alias="testuser",
    )
    return user


@pytest.fixture(autouse=True)
def _override_session() -> Generator[None, None, None]:
    """Override get_session with a no-op mock to avoid requiring a real database."""
    app.dependency_overrides[get_session] = lambda: MagicMock(spec=AsyncSession)
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture(autouse=True)
def _override_auth(mock_user: User) -> None:
    app.dependency_overrides[require_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(require_current_user, None)


async def test_get_me(client: AsyncClient, mock_user: User) -> None:
    """GET /api/v1/users/me should return the current user's profile."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_user.id
    assert data["email"] == mock_user.email
    assert data["name"] == mock_user.name
    assert data["role"] == mock_user.role.value
    assert data["github_alias"] == mock_user.github_alias
    assert data["is_active"] is True


async def test_update_me(client: AsyncClient, mock_user: User) -> None:
    """PATCH /api/v1/users/me should update the current user's profile."""
    with patch("services.users.UsersService.update_me", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            "id": 1,
            "email": "test@tul.cz",
            "name": "Updated Name",
            "role": "STUDENT",
            "github_alias": "updated-alias",
            "is_active": True,
        }
        response = await client.patch(
            "/api/v1/users/me",
            json={"name": "Updated Name", "github_alias": "updated-alias"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["github_alias"] == "updated-alias"
    assert data["is_active"] is True


async def test_list_users_as_student_denied(client: AsyncClient) -> None:
    """GET /api/v1/users should be denied for non-admin users."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 403


async def test_list_users_as_admin(client: AsyncClient) -> None:
    """GET /api/v1/users should return all users for an admin."""
    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    mock_users = [
        {
            "id": 1,
            "email": "u1@tul.cz",
            "name": "U1",
            "role": "STUDENT",
            "github_alias": None,
            "is_active": True,
        },
        {
            "id": 2,
            "email": "admin@tul.cz",
            "name": "Admin",
            "role": "ADMIN",
            "github_alias": None,
            "is_active": True,
        },
    ]

    with patch("services.users.UsersService.get_users", new_callable=AsyncMock) as mock_get_users:
        mock_get_users.return_value = mock_users
        response = await client.get("/api/v1/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["email"] == "u1@tul.cz"
    assert data[0]["is_active"] is True


async def test_create_user_as_admin(client: AsyncClient) -> None:
    """POST /api/v1/users should create a new user when called by an admin."""
    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    new_user_data = {
        "email": "new@tul.cz",
        "name": "New User",
        "role": "STUDENT",
    }

    with patch("services.users.UsersService.create_user", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            "id": 3,
            "email": "new@tul.cz",
            "name": "New User",
            "role": "STUDENT",
            "github_alias": None,
            "is_active": True,
        }
        response = await client.post("/api/v1/users", json=new_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@tul.cz"
    assert data["id"] == 3


async def test_deactivate_user_as_admin(client: AsyncClient) -> None:
    """PATCH /api/v1/users/{id} should allow an admin to deactivate a user."""
    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    with patch("services.users.UsersService.update_user", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            "id": 1,
            "email": "test@tul.cz",
            "name": "Test User",
            "role": "STUDENT",
            "github_alias": "testuser",
            "is_active": False,
        }
        response = await client.patch("/api/v1/users/1", json={"is_active": False})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["is_active"] is False


async def test_get_user_by_id_as_admin(client: AsyncClient) -> None:
    """GET /api/v1/users/{id} should return the user when called by an admin."""
    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    with patch("services.users.UsersService.get_user", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {
            "id": 1,
            "email": "test@tul.cz",
            "name": "Test User",
            "role": "STUDENT",
            "github_alias": "testuser",
            "is_active": True,
        }
        response = await client.get("/api/v1/users/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == "test@tul.cz"
    assert data["is_active"] is True


async def test_get_user_by_id_not_found(client: AsyncClient) -> None:
    """GET /api/v1/users/{id} should return 404 when the user does not exist."""
    from services.users import UserNotFoundError

    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    with patch("services.users.UsersService.get_user", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = UserNotFoundError("User 99 not found.")
        response = await client.get("/api/v1/users/99")

    assert response.status_code == 404


async def test_get_user_by_id_as_non_admin(client: AsyncClient) -> None:
    """GET /api/v1/users/{id} should return 403 when called by a non-admin."""
    from services.users import PermissionDeniedError

    with patch("services.users.UsersService.get_user", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = PermissionDeniedError("Only admins can view other users.")
        response = await client.get("/api/v1/users/1")

    assert response.status_code == 403


async def test_update_user_by_id_as_admin(client: AsyncClient) -> None:
    """PATCH /api/v1/users/{id} should allow an admin to update a user's role."""
    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    with patch("services.users.UsersService.update_user", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            "id": 1,
            "email": "test@tul.cz",
            "name": "Test User",
            "role": "LECTURER",
            "github_alias": "testuser",
            "is_active": True,
        }
        response = await client.patch("/api/v1/users/1", json={"role": "LECTURER"})

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "LECTURER"


async def test_update_user_by_id_not_found(client: AsyncClient) -> None:
    """PATCH /api/v1/users/{id} should return 404 when the user does not exist."""
    from services.users import UserNotFoundError

    admin_user = User(id=2, email="admin@tul.cz", name="Admin", role=UserRole.ADMIN)
    app.dependency_overrides[require_current_user] = lambda: admin_user

    with patch("services.users.UsersService.update_user", new_callable=AsyncMock) as mock_update:
        mock_update.side_effect = UserNotFoundError("User 99 not found.")
        response = await client.patch("/api/v1/users/99", json={"is_active": False})

    assert response.status_code == 404
