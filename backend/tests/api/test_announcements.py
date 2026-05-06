from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_current_user
from db.session import get_session
from main import app
from models.announcement import AnnouncementSeverity
from models.user import User, UserRole
from schemas.announcements import AnnouncementPublic


@pytest.fixture
def admin_user() -> User:
    return User(id=1, email="admin@tul.cz", name="Admin User", role=UserRole.ADMIN)


@pytest.fixture
def student_user() -> User:
    return User(id=2, email="student@tul.cz", name="Student User", role=UserRole.STUDENT)


@pytest.fixture(autouse=True)
def _override_session() -> Generator[None, None, None]:
    """Replace the DB session dependency with a mock to avoid hitting a real database."""
    app.dependency_overrides[get_session] = lambda: MagicMock(spec=AsyncSession)
    yield
    app.dependency_overrides.pop(get_session, None)


def _set_auth(user: User) -> None:
    app.dependency_overrides[require_current_user] = lambda: user


def _clear_auth() -> None:
    app.dependency_overrides.pop(require_current_user, None)


# ---------------------------------------------------------------------------
# Public: GET /api/v1/announcements/active
# ---------------------------------------------------------------------------


async def test_get_active_announcement_returns_active(client: AsyncClient) -> None:
    """GET /api/v1/announcements/active returns the active announcement when one exists."""
    active = AnnouncementPublic(
        id=1,
        message="Maintenance on Sunday.",
        severity=AnnouncementSeverity.WARNING,
        is_active=True,
        created_at="2026-05-01T10:00:00Z",
        updated_at="2026-05-01T10:00:00Z",
    )
    with patch(
        "services.announcements.AnnouncementsService.get_active",
        new_callable=AsyncMock,
        return_value=active,
    ):
        response = await client.get("/api/v1/announcements/active")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["message"] == "Maintenance on Sunday."
    assert data["severity"] == "WARNING"
    assert data["is_active"] is True


async def test_get_active_announcement_returns_null_when_none(client: AsyncClient) -> None:
    """GET /api/v1/announcements/active returns null when no active announcement exists."""
    with patch(
        "services.announcements.AnnouncementsService.get_active",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await client.get("/api/v1/announcements/active")

    assert response.status_code == 200
    assert response.json() is None


# ---------------------------------------------------------------------------
# Admin: GET /api/v1/announcements
# ---------------------------------------------------------------------------


async def test_get_all_announcements_as_admin(client: AsyncClient, admin_user: User) -> None:
    """Admin can list all announcements."""
    _set_auth(admin_user)
    try:
        announcements = [
            AnnouncementPublic(
                id=1,
                message="A",
                severity=AnnouncementSeverity.INFO,
                is_active=True,
                created_at="2026-05-01T10:00:00Z",
                updated_at="2026-05-01T10:00:00Z",
            )
        ]
        with patch(
            "services.announcements.AnnouncementsService.get_all",
            new_callable=AsyncMock,
            return_value=announcements,
        ):
            response = await client.get("/api/v1/announcements")

        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        _clear_auth()


async def test_get_all_announcements_as_student_returns_403(
    client: AsyncClient, student_user: User
) -> None:
    """Non-admin users receive 403 when attempting to list all announcements."""
    _set_auth(student_user)
    try:
        with patch(
            "services.announcements.AnnouncementsService.get_all",
            new_callable=AsyncMock,
            side_effect=__import__(
                "services.announcements", fromlist=["PermissionDeniedError"]
            ).PermissionDeniedError,
        ):
            response = await client.get("/api/v1/announcements")

        assert response.status_code == 403
    finally:
        _clear_auth()


# ---------------------------------------------------------------------------
# Admin: POST /api/v1/announcements
# ---------------------------------------------------------------------------


async def test_create_announcement_as_admin(client: AsyncClient, admin_user: User) -> None:
    """Admin can create a new announcement."""
    _set_auth(admin_user)
    try:
        created = AnnouncementPublic(
            id=5,
            message="Deadline extended.",
            severity=AnnouncementSeverity.INFO,
            is_active=False,
            created_at="2026-05-06T12:00:00Z",
            updated_at="2026-05-06T12:00:00Z",
        )
        with patch(
            "services.announcements.AnnouncementsService.create",
            new_callable=AsyncMock,
            return_value=created,
        ):
            response = await client.post(
                "/api/v1/announcements",
                json={"message": "Deadline extended.", "severity": "INFO", "is_active": False},
            )

        assert response.status_code == 201
        assert response.json()["id"] == 5
    finally:
        _clear_auth()


# ---------------------------------------------------------------------------
# Admin: PATCH /api/v1/announcements/{id}
# ---------------------------------------------------------------------------


async def test_update_announcement_as_admin(client: AsyncClient, admin_user: User) -> None:
    """Admin can partially update an announcement."""
    _set_auth(admin_user)
    try:
        updated = AnnouncementPublic(
            id=1,
            message="Updated message.",
            severity=AnnouncementSeverity.ERROR,
            is_active=True,
            created_at="2026-05-01T10:00:00Z",
            updated_at="2026-05-06T12:00:00Z",
        )
        with patch(
            "services.announcements.AnnouncementsService.update",
            new_callable=AsyncMock,
            return_value=updated,
        ):
            response = await client.patch(
                "/api/v1/announcements/1",
                json={"message": "Updated message.", "severity": "ERROR"},
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Updated message."
        assert response.json()["severity"] == "ERROR"
    finally:
        _clear_auth()


# ---------------------------------------------------------------------------
# Admin: DELETE /api/v1/announcements/{id}
# ---------------------------------------------------------------------------


async def test_delete_announcement_as_admin(client: AsyncClient, admin_user: User) -> None:
    """Admin can delete an announcement and receives 204."""
    _set_auth(admin_user)
    try:
        with patch(
            "services.announcements.AnnouncementsService.delete",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.delete("/api/v1/announcements/1")

        assert response.status_code == 204
    finally:
        _clear_auth()


async def test_delete_nonexistent_announcement_returns_404(
    client: AsyncClient, admin_user: User
) -> None:
    """Deleting a non-existent announcement returns 404."""
    from services.announcements import AnnouncementNotFoundError

    _set_auth(admin_user)
    try:
        with patch(
            "services.announcements.AnnouncementsService.delete",
            new_callable=AsyncMock,
            side_effect=AnnouncementNotFoundError("Not found."),
        ):
            response = await client.delete("/api/v1/announcements/999")

        assert response.status_code == 404
    finally:
        _clear_auth()
