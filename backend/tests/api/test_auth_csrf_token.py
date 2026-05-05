from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_current_user
from db.session import get_session
from main import app
from models import User
from models.user import UserRole


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _override_session() -> Generator[None, None, None]:
    app.dependency_overrides[get_session] = lambda: MagicMock(spec=AsyncSession)
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture(autouse=True)
def _mock_settings() -> Generator[None, None, None]:
    mock_settings = MagicMock()
    mock_settings.app_env = "local"
    with patch("api.auth.get_settings", return_value=mock_settings):
        yield


def _make_user(user_id: int = 1) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = UserRole.STUDENT
    return user


# ---------------------------------------------------------------------------
# GET /api/v1/auth/csrf-token
# ---------------------------------------------------------------------------


async def test_csrf_token_returns_401_when_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/auth/csrf-token must return 401 when no session exists."""
    # No require_current_user override → the real dependency raises 401.
    response = await client.get("/api/v1/auth/csrf-token")
    assert response.status_code == 401


async def test_csrf_token_returns_200_with_token_for_authenticated_user(
    client: AsyncClient,
) -> None:
    """Returns 200 with an xsrf_token string in the body for an active session."""
    app.dependency_overrides[require_current_user] = lambda: _make_user()
    try:
        response = await client.get("/api/v1/auth/csrf-token")
    finally:
        app.dependency_overrides.pop(require_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert "xsrf_token" in body
    assert isinstance(body["xsrf_token"], str) and len(body["xsrf_token"]) > 0


async def test_csrf_token_sets_non_httponly_cookie(client: AsyncClient) -> None:
    """The XSRF-TOKEN cookie must be readable by JavaScript (not HttpOnly)."""
    app.dependency_overrides[require_current_user] = lambda: _make_user()
    try:
        response = await client.get("/api/v1/auth/csrf-token")
    finally:
        app.dependency_overrides.pop(require_current_user, None)

    set_cookie_headers = response.headers.get_list("set-cookie")
    xsrf_header = next((h for h in set_cookie_headers if "XSRF-TOKEN=" in h), "")
    assert xsrf_header, "XSRF-TOKEN Set-Cookie header not found"
    assert "httponly" not in xsrf_header.lower()
    assert "samesite=lax" in xsrf_header.lower()


async def test_csrf_token_body_matches_cookie(client: AsyncClient) -> None:
    """The xsrf_token in the body must equal the XSRF-TOKEN cookie value."""
    app.dependency_overrides[require_current_user] = lambda: _make_user()
    try:
        response = await client.get("/api/v1/auth/csrf-token")
    finally:
        app.dependency_overrides.pop(require_current_user, None)

    assert response.json()["xsrf_token"] == response.cookies["XSRF-TOKEN"]


async def test_csrf_token_each_call_generates_unique_token(client: AsyncClient) -> None:
    """Each call must produce a different token (tokens are not reused)."""
    app.dependency_overrides[require_current_user] = lambda: _make_user()
    try:
        r1 = await client.get("/api/v1/auth/csrf-token")
        r2 = await client.get("/api/v1/auth/csrf-token")
    finally:
        app.dependency_overrides.pop(require_current_user, None)

    assert r1.json()["xsrf_token"] != r2.json()["xsrf_token"]
