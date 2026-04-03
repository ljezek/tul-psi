from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_settings() -> Generator[None, None, None]:
    """Stub application settings so tests do not require a real environment."""
    mock_settings = MagicMock()
    # Use "local" so the route does not set the Secure flag on the cookie — the
    # test HTTP client uses plain HTTP, and a Secure cookie would be dropped.
    mock_settings.app_env = "local"
    with patch("api.auth.get_settings", return_value=mock_settings):
        yield


# ---------------------------------------------------------------------------
# Logout endpoint
# ---------------------------------------------------------------------------


async def test_logout_returns_200(client: AsyncClient) -> None:
    """POST /api/v1/auth/logout must return HTTP 200."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200


async def test_logout_returns_empty_body(client: AsyncClient) -> None:
    """POST /api/v1/auth/logout must return an empty JSON object."""
    response = await client.post("/api/v1/auth/logout")
    assert response.json() == {}


async def test_logout_sets_session_cookie_with_max_age_zero(client: AsyncClient) -> None:
    """POST /api/v1/auth/logout must set the ``session`` cookie with ``Max-Age=0``."""
    response = await client.post("/api/v1/auth/logout")
    # httpx stores the Set-Cookie attributes in response.headers; inspect the raw header
    # because the cookie jar discards expired cookies (Max-Age=0) automatically.
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "session=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header


async def test_logout_cookie_is_httponly(client: AsyncClient) -> None:
    """The cookie set by the logout endpoint must carry the ``HttpOnly`` flag."""
    response = await client.post("/api/v1/auth/logout")
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "httponly" in set_cookie_header.lower()


async def test_logout_cookie_has_samesite_strict(client: AsyncClient) -> None:
    """The cookie set by the logout endpoint must use ``SameSite=strict``."""
    response = await client.post("/api/v1/auth/logout")
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "samesite=strict" in set_cookie_header.lower()


async def test_logout_is_idempotent_without_session(client: AsyncClient) -> None:
    """Calling logout without an active session must still return HTTP 200."""
    # No cookie set on the client — simulates a logged-out or anonymous caller.
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
