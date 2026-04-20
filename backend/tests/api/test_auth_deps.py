from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException, Request
from httpx import AsyncClient

from api.deps import get_current_user, get_optional_current_user, verify_csrf_token
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
    request = MagicMock(spec=Request)
    request.cookies = {}
    session = AsyncMock()

    result = await get_current_user(request, session)

    assert result is None


async def test_get_current_user_returns_user_for_valid_token() -> None:
    """``get_current_user`` must return the matching ``User`` for a valid JWT."""
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
        mock_settings.return_value.jwt_algorithm = "HS256"
        result = await get_current_user(request, session)

    assert result is user


async def test_get_current_user_raises_401_for_invalid_token() -> None:
    """``get_current_user`` must raise HTTP 401 when the JWT signature is invalid."""
    request = MagicMock(spec=Request)
    request.cookies = {"session": "not-a-valid-jwt"}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        mock_settings.return_value.jwt_algorithm = "HS256"
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_raises_401_for_missing_user_id_in_payload() -> None:
    """``get_current_user`` must raise HTTP 401 when the JWT payload lacks ``user_id``."""
    token = _make_token({"role": "STUDENT"})  # No user_id field.

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        mock_settings.return_value.jwt_algorithm = "HS256"
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_raises_401_when_user_not_in_db() -> None:
    """``get_current_user`` must raise HTTP 401 when the JWT user_id has no DB record."""
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
        mock_settings.return_value.jwt_algorithm = "HS256"
        await get_current_user(request, session)

    assert exc_info.value.status_code == 401


async def test_get_current_user_raises_401_for_non_integer_user_id() -> None:
    """``get_current_user`` must raise HTTP 401 when ``user_id`` in the payload is not an int."""
    token = _make_token({"user_id": "not-an-int", "role": "STUDENT"})

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        pytest.raises(HTTPException) as exc_info,
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        mock_settings.return_value.jwt_algorithm = "HS256"
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
    """A tampered ``session`` cookie must result in HTTP 401 on any protected endpoint.

    Protected endpoints use ``require_current_user`` which raises HTTP 401 for
    unauthenticated requests.  Public endpoints that use ``get_optional_current_user``
    gracefully degrade to the unauthenticated response instead.
    """
    # Override get_session so the DB is not required for this test.
    app.dependency_overrides[get_session] = _mock_get_session
    client.cookies.set("session", "eyJ.tampered.jwt")
    with patch("api.deps.get_settings") as mock_settings:
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        # Use a protected endpoint (PATCH /projects/{id}) that requires authentication.
        response = await client.patch("/api/v1/projects/1", json={"title": "x"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Unit tests for the get_optional_current_user dependency
# ---------------------------------------------------------------------------


async def test_get_optional_current_user_returns_none_for_expired_token() -> None:
    """``get_optional_current_user`` must return ``None`` for an expired JWT, not raise."""
    expired_token = jwt.encode(
        {"user_id": 1, "exp": datetime.now(UTC) - timedelta(days=1)},
        _JWT_SECRET,
        algorithm="HS256",
    )

    request = MagicMock(spec=Request)
    request.cookies = {"session": expired_token}
    session = AsyncMock()

    with patch("api.deps.get_settings") as mock_settings:
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        mock_settings.return_value.jwt_algorithm = "HS256"
        result = await get_optional_current_user(request, session)

    assert result is None


async def test_get_optional_current_user_returns_none_for_invalid_token() -> None:
    """``get_optional_current_user`` must return ``None`` for a tampered JWT, not raise."""
    request = MagicMock(spec=Request)
    request.cookies = {"session": "not-a-valid-jwt"}
    session = AsyncMock()

    with patch("api.deps.get_settings") as mock_settings:
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        mock_settings.return_value.jwt_algorithm = "HS256"
        result = await get_optional_current_user(request, session)

    assert result is None


async def test_get_optional_current_user_returns_none_without_cookie() -> None:
    """``get_optional_current_user`` must return ``None`` when no ``session`` cookie is present."""
    request = MagicMock(spec=Request)
    request.cookies = {}
    session = AsyncMock()

    result = await get_optional_current_user(request, session)

    assert result is None


# ---------------------------------------------------------------------------
# Unit tests for verify_csrf_token
# ---------------------------------------------------------------------------


async def test_verify_csrf_token_skips_safe_methods() -> None:
    """GET, HEAD, OPTIONS, and TRACE must bypass CSRF validation entirely."""
    for method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        request = MagicMock(spec=Request)
        request.method = method
        await verify_csrf_token(request)


async def test_verify_csrf_token_allows_post_without_cookie() -> None:
    """POST with no XSRF-TOKEN cookie must pass — auth deps handle unauthenticated requests."""
    request = MagicMock(spec=Request)
    request.method = "POST"
    request.cookies = {}
    await verify_csrf_token(request)


async def test_verify_csrf_token_passes_when_header_matches_cookie() -> None:
    """POST with a matching XSRF-TOKEN cookie and X-XSRF-Token header must pass."""
    token = "a1b2c3d4e5f6"  # noqa: S105
    request = MagicMock(spec=Request)
    request.method = "POST"
    request.cookies = {"XSRF-TOKEN": token}
    request.headers = {"X-XSRF-Token": token}
    await verify_csrf_token(request)


async def test_verify_csrf_token_raises_403_on_header_mismatch() -> None:
    """POST with a mismatched X-XSRF-Token header must raise HTTP 403."""
    request = MagicMock(spec=Request)
    request.method = "POST"
    request.cookies = {"XSRF-TOKEN": "correct"}
    request.headers = {"X-XSRF-Token": "wrong"}
    with pytest.raises(HTTPException) as exc_info:
        await verify_csrf_token(request)
    assert exc_info.value.status_code == 403


async def test_verify_csrf_token_raises_403_on_missing_header() -> None:
    """POST with XSRF-TOKEN cookie but no X-XSRF-Token header must raise HTTP 403."""
    request = MagicMock(spec=Request)
    request.method = "POST"
    request.cookies = {"XSRF-TOKEN": "secret"}
    request.headers = {}
    with pytest.raises(HTTPException) as exc_info:
        await verify_csrf_token(request)
    assert exc_info.value.status_code == 403


async def test_verify_csrf_token_enforces_delete_and_patch() -> None:
    """DELETE and PATCH requests with a mismatched token must also raise HTTP 403."""
    for method in ("DELETE", "PATCH"):
        request = MagicMock(spec=Request)
        request.method = method
        request.cookies = {"XSRF-TOKEN": "secret"}
        request.headers = {"X-XSRF-Token": "wrong"}
        with pytest.raises(HTTPException) as exc_info:
            await verify_csrf_token(request)
        assert exc_info.value.status_code == 403


async def test_get_optional_current_user_returns_user_for_valid_token() -> None:
    """``get_optional_current_user`` must return the matching ``User`` for a valid JWT."""
    user = _make_user(user_id=3)
    token = _make_token({"user_id": 3, "role": "STUDENT"})

    request = MagicMock(spec=Request)
    request.cookies = {"session": token}
    session = AsyncMock()

    with (
        patch("api.deps.get_settings") as mock_settings,
        patch("api.deps.get_user_by_id", new_callable=AsyncMock, return_value=user),
    ):
        mock_settings.return_value.jwt_secret = _JWT_SECRET
        mock_settings.return_value.jwt_algorithm = "HS256"
        result = await get_optional_current_user(request, session)

    assert result is user
