from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from httpx import AsyncClient

from api.deps import get_current_user
from db.session import get_session
from main import app
from models.user import User, UserRole

# ---------------------------------------------------------------------------
# Unit tests for the get_current_user dependency
# ---------------------------------------------------------------------------

_JWT_SECRET = "test-secret-that-is-long-enough-for-hmac-sha256"  # noqa: S105


def _make_user(user_id: int = 1, role: UserRole = UserRole.STUDENT) -> User:
    """Return a minimal ``User`` instance for testing."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "student@tul.cz"
    user.role = role
    return user


def _make_token(payload: dict, secret: str = _JWT_SECRET) -> str:
    """Encode and return a JWT string for the given *payload*."""
    return jwt.encode(payload, secret, algorithm="HS256")


async def test_get_current_user_returns_none_without_cookie() -> None:
    """``get_current_user`` must return ``None`` when no ``session`` cookie is present."""
    from fastapi import Request

    request = MagicMock(spec=Request)
    request.cookies = {}
    session = AsyncMock()

    result = await get_current_user(request, session)

    assert result is None


async def test_get_current_user_returns_user_for_valid_token() -> None:
    """``get_current_user`` must return the matching ``User`` for a valid JWT."""
    from fastapi import Request

    user = _make_user(user_id=7)
    token = _make_token({"user_id": 7, "role": "STUDENT"})

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        patch("api.deps.get_user_by_id", new_callable=AsyncMock, return_value=user),
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        result = await get_current_user(request, session)

    assert result is user


async def test_get_current_user_raises_401_for_invalid_token() -> None:
    """``get_current_user`` must raise HTTP 401 when the JWT signature is invalid."""
    from fastapi import HTTPException, Request

    request = MagicMock(spec=Request)
    request.cookies = {"session": "not-a-valid-jwt"}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_raises_401_for_missing_user_id_in_payload() -> None:
    """``get_current_user`` must raise HTTP 401 when the JWT payload lacks ``user_id``."""
    from fastapi import HTTPException, Request

    token = _make_token({"role": "STUDENT"})  # No user_id field.

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_raises_401_when_user_not_in_db() -> None:
    """``get_current_user`` must raise HTTP 401 when the JWT user_id has no DB record."""
    from fastapi import HTTPException, Request

    token = _make_token({"user_id": 999, "role": "STUDENT"})

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        patch("api.deps.get_user_by_id", new_callable=AsyncMock, return_value=None),
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_raises_401_for_non_integer_user_id() -> None:
    """``get_current_user`` must raise HTTP 401 when ``user_id`` in the payload is not an int."""
    from fastapi import HTTPException, Request

    token = _make_token({"user_id": "not-an-int", "role": "STUDENT"})

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Integration-style tests via the HTTP client
# ---------------------------------------------------------------------------


async def _mock_get_session() -> AsyncMock:
    """Async generator mock for the ``get_session`` dependency."""
    yield AsyncMock()


@pytest.fixture(autouse=True)
def _clear_dep_overrides():
    """Remove all dependency overrides after every test."""
    yield
    app.dependency_overrides.clear()


async def test_endpoint_returns_401_for_tampered_cookie(client: AsyncClient) -> None:
    """A tampered ``session`` cookie must result in HTTP 401 on any protected endpoint."""
    # Override get_session so the DB is not required for this test.
    app.dependency_overrides[get_session] = _mock_get_session
    with patch("api.deps.get_settings") as mock_settings:
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        response = await client.get("/api/v1/projects/1", cookies={"session": "eyJ.tampered.jwt"})
    assert response.status_code == 401
