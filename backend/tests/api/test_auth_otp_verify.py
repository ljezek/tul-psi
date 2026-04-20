from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from main import app
from models import OtpToken, User
from models.user import UserRole

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_JWT_SECRET = "test-secret-that-is-long-enough-for-hmac-sha256"  # noqa: S105


@pytest.fixture(autouse=True)
def _override_session() -> Generator[None, None, None]:
    """Override get_session with a no-op mock to avoid requiring a real database."""
    app.dependency_overrides[get_session] = lambda: MagicMock(spec=AsyncSession)
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture(autouse=True)
def _mock_settings() -> Generator[None, None, None]:
    """Stub settings consumed by the OTP-verify flow across all tests in this module.

    Three distinct settings values are exercised:
    - ``jwt_secret`` / ``jwt_algorithm``: used by ``_create_jwt`` to sign the session token;
      tests decode the resulting cookie to verify the payload, so they need the same secret.
    - ``app_env="local"``: prevents the route from setting the ``Secure`` flag on the cookie;
      the test client uses plain HTTP so a Secure cookie would be silently dropped.
    """
    mock_settings = MagicMock()
    mock_settings.jwt_secret = _JWT_SECRET
    mock_settings.jwt_algorithm = "HS256"
    # Use "local" so the route does not set the Secure flag on the cookie — the
    # test HTTP client uses plain HTTP, and a Secure cookie would be dropped.
    mock_settings.app_env = "local"
    with (
        patch("services.auth_service.get_settings", return_value=mock_settings),
        patch("api.auth.get_settings", return_value=mock_settings),
    ):
        yield


def _make_user(user_id: int = 1, role: UserRole = UserRole.STUDENT) -> MagicMock:
    """Return a mock User with the given id and role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = role
    return user


def _make_token(user_id: int = 1, otp: str = "123456", attempts: int = 0) -> MagicMock:
    """Return a mock OtpToken with a bcrypt hash of *otp*."""
    token = MagicMock(spec=OtpToken)
    token.id = 99
    token.user_id = user_id
    token.token_hash = bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
    token.attempts = attempts
    token.used = False
    token.expires_at = datetime.now(UTC) + timedelta(minutes=10)
    return token


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------


async def test_otp_verify_rejects_non_tul_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/otp/verify must return 422 for non-@tul.cz addresses."""
    response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"email": "student@gmail.com", "otp": "123456"},
    )
    assert response.status_code == 422


async def test_otp_verify_rejects_malformed_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/otp/verify must return 422 for addresses that are not valid e-mails."""
    response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"email": "not-an-email", "otp": "123456"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 401 — invalid / expired code
# ---------------------------------------------------------------------------


async def test_otp_verify_returns_401_for_unknown_email(client: AsyncClient) -> None:
    """Returns 401 when no user exists for the supplied e-mail."""
    with patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=None):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "nobody@tul.cz", "otp": "000000"},
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired code"


async def test_otp_verify_returns_401_when_no_active_token(client: AsyncClient) -> None:
    """Returns 401 when the user exists but has no active (unused, unexpired) token."""
    mock_user = _make_user()
    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.get_active_otp_token", new_callable=AsyncMock, return_value=None),
    ):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "jan.novak@tul.cz", "otp": "000000"},
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired code"


async def test_otp_verify_returns_401_for_wrong_otp(client: AsyncClient) -> None:
    """Returns 401 when the supplied OTP does not match the stored hash."""
    mock_user = _make_user()
    mock_token = _make_token(otp="999999")
    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.get_active_otp_token", new_callable=AsyncMock, return_value=mock_token),
        patch(
            "db.auth.increment_otp_attempts", new_callable=AsyncMock, return_value=1
        ) as mock_increment,
        patch("db.auth.mark_otp_token_used", new_callable=AsyncMock),
    ):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "jan.novak@tul.cz", "otp": "000000"},
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired code"
    mock_increment.assert_called_once()


# ---------------------------------------------------------------------------
# 429 — too many attempts
# ---------------------------------------------------------------------------


async def test_otp_verify_returns_429_when_attempt_limit_reached(client: AsyncClient) -> None:
    """Returns 429 when a wrong OTP brings the attempt count to the maximum."""
    mock_user = _make_user()
    mock_token = _make_token(otp="999999")
    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.get_active_otp_token", new_callable=AsyncMock, return_value=mock_token),
        # Simulate the 5th failed attempt being recorded.
        patch("db.auth.increment_otp_attempts", new_callable=AsyncMock, return_value=5),
        patch("db.auth.mark_otp_token_used", new_callable=AsyncMock) as mock_mark_used,
    ):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "jan.novak@tul.cz", "otp": "000000"},
        )
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many attempts — request a new OTP code"
    # Token must be invalidated so it cannot be resubmitted.
    mock_mark_used.assert_called_once()


# ---------------------------------------------------------------------------
# 200 — success
# ---------------------------------------------------------------------------


async def test_otp_verify_success_sets_cookie_and_marks_token_used(
    client: AsyncClient,
) -> None:
    """A valid OTP must return 200 with an empty body, set the session cookie, and mark the token
    used."""
    mock_user = _make_user()
    mock_token = _make_token(otp="483921")
    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.get_active_otp_token", new_callable=AsyncMock, return_value=mock_token),
        patch("db.auth.mark_otp_token_used", new_callable=AsyncMock) as mock_mark_used,
    ):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "jan.novak@tul.cz", "otp": "483921"},
        )
    assert response.status_code == 200
    assert response.json() == {}
    assert "session" in response.cookies
    mock_mark_used.assert_called_once()
    assert mock_mark_used.call_args[0][1] == mock_token.id


async def test_otp_verify_success_sets_xsrf_cookie(client: AsyncClient) -> None:
    """Successful OTP verification must set non-HttpOnly XSRF-TOKEN cookie for CSRF protection."""
    mock_user = _make_user()
    mock_token = _make_token(otp="483921")
    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.get_active_otp_token", new_callable=AsyncMock, return_value=mock_token),
        patch("db.auth.mark_otp_token_used", new_callable=AsyncMock),
    ):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "jan.novak@tul.cz", "otp": "483921"},
        )
    assert response.status_code == 200
    assert "XSRF-TOKEN" in response.cookies
    set_cookie_headers = response.headers.get_list("set-cookie")
    xsrf_header = next((h for h in set_cookie_headers if "XSRF-TOKEN=" in h), "")
    assert xsrf_header, "XSRF-TOKEN Set-Cookie header not found"
    assert "httponly" not in xsrf_header.lower()
    assert "samesite=strict" in xsrf_header.lower()


async def test_otp_verify_jwt_claims_and_expiry(client: AsyncClient) -> None:
    """The session cookie JWT must carry user_id and role claims and expire in ~8 hours."""
    mock_user = _make_user(user_id=42, role=UserRole.STUDENT)
    mock_token = _make_token(otp="483921")
    before = datetime.now(UTC)
    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.get_active_otp_token", new_callable=AsyncMock, return_value=mock_token),
        patch("db.auth.mark_otp_token_used", new_callable=AsyncMock),
    ):
        response = await client.post(
            "/api/v1/auth/otp/verify",
            json={"email": "jan.novak@tul.cz", "otp": "483921"},
        )
    token_value = response.cookies["session"]
    payload = jwt.decode(token_value, _JWT_SECRET, algorithms=["HS256"])
    assert payload["user_id"] == 42
    assert payload["role"] == UserRole.STUDENT.value
    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
    assert timedelta(hours=7, minutes=59) <= (exp - before) <= timedelta(hours=8, seconds=5), (
        f"JWT expiry {exp} is not approximately 8 hours after {before}."
    )
