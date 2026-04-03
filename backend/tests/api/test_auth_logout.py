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


async def test_logout_success(client: AsyncClient) -> None:
    """POST /api/v1/auth/logout must return HTTP 200 with an empty JSON body."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json() == {}


async def test_logout_cookie_attributes(client: AsyncClient) -> None:
    """The ``session`` cookie returned by logout must have Max-Age=0, HttpOnly, and SameSite=strict.

    httpx discards expired cookies (Max-Age=0) from its cookie jar automatically,
    so the raw ``Set-Cookie`` response header is inspected instead.
    """
    response = await client.post("/api/v1/auth/logout")
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "session=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header
    assert "httponly" in set_cookie_header.lower()
    assert "samesite=strict" in set_cookie_header.lower()


async def test_logout_is_idempotent_without_session(client: AsyncClient) -> None:
    """Calling logout without an active session must still return HTTP 200."""
    # No cookie set on the client — simulates a logged-out or anonymous caller.
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
