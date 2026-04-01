from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from httpx import AsyncClient
from sqlmodel import Session

from db.session import get_session
from main import app
from models import OtpToken

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _override_session() -> Generator[None, None, None]:
    """Override get_session with a no-op mock to avoid requiring a real database.

    Individual tests that need to inspect DB interactions should patch the
    ``db.auth`` module functions directly instead of configuring the session.
    """
    app.dependency_overrides[get_session] = lambda: MagicMock(spec=Session)
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture(autouse=True)
def _mock_settings() -> Generator[None, None, None]:
    """Stub application settings so tests do not require a real database URL."""
    mock_settings = MagicMock()
    # Ensure dev-only OTP display is disabled; otherwise a truthy MagicMock attribute
    # could cause tests to print OTPs to stderr and become flaky.
    mock_settings.show_otp_dev_only = False
    with patch("services.auth_service.get_settings", return_value=mock_settings):
        yield


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------


async def test_otp_request_rejects_non_tul_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/otp/request must return 422 for non-@tul.cz addresses."""
    response = await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "student@gmail.com"},
    )
    assert response.status_code == 422


async def test_otp_request_rejects_malformed_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/otp/request must return 422 for addresses that are not valid e-mails."""
    response = await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422


async def test_otp_request_rejects_tul_cz_subdomain(client: AsyncClient) -> None:
    """A subdomain like @sub.tul.cz must not be accepted — only @tul.cz is valid."""
    response = await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "user@sub.tul.cz"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Silent-success behaviour (registered & unregistered addresses)
# ---------------------------------------------------------------------------


async def test_otp_request_returns_200_for_unknown_email(client: AsyncClient) -> None:
    """Returns HTTP 200 even when no matching user exists (prevents user enumeration)."""
    with patch("db.auth.get_user_by_email", return_value=None):
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "unknown@tul.cz"},
        )
    assert response.status_code == 200
    assert "OTP" in response.json()["message"]


async def test_otp_request_returns_200_for_registered_email(client: AsyncClient) -> None:
    """Returns HTTP 200 when a matching user is found and the OTP is stored."""
    mock_user = MagicMock()
    mock_user.id = 1
    with (
        patch("db.auth.get_user_by_email", return_value=mock_user),
        patch("db.auth.invalidate_active_otp_tokens"),
        patch("db.auth.add_otp_token"),
    ):
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "jan.novak@tul.cz"},
        )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# OTP storage (unit-level)
# ---------------------------------------------------------------------------


async def test_otp_request_stores_token_for_registered_user(client: AsyncClient) -> None:
    """The stored OtpToken has the correct user_id, timestamps, and a valid bcrypt hash."""
    mock_user = MagicMock()
    mock_user.id = 42

    with (
        patch("db.auth.get_user_by_email", return_value=mock_user),
        patch("db.auth.invalidate_active_otp_tokens"),
        patch("db.auth.add_otp_token") as mock_save,
        patch("services.auth_service._generate_otp", return_value="483921"),
    ):
        before = datetime.now(UTC)
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "jan.novak@tul.cz"},
        )
        after = datetime.now(UTC)

    mock_save.assert_called_once()
    # add_otp_token(session, token) — token is the second positional argument.
    token: OtpToken = mock_save.call_args[0][1]

    assert token.user_id == 42
    assert before <= token.created_at <= after + timedelta(seconds=1)
    assert (
        timedelta(minutes=14, seconds=59)
        <= (token.expires_at - token.created_at)
        <= timedelta(minutes=15, seconds=1)
    )
    assert bcrypt.checkpw(b"483921", token.token_hash.encode())


async def test_otp_request_invalidates_old_tokens_for_user(client: AsyncClient) -> None:
    """A new OTP request must call invalidate_active_otp_tokens for the same user."""
    mock_user = MagicMock()
    mock_user.id = 42

    with (
        patch("db.auth.get_user_by_email", return_value=mock_user),
        patch("db.auth.invalidate_active_otp_tokens") as mock_invalidate,
        patch("db.auth.add_otp_token"),
    ):
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "jan.novak@tul.cz"},
        )

    mock_invalidate.assert_called_once()
    # invalidate_active_otp_tokens(session, user_id) — user_id is the second positional arg.
    user_id_arg = mock_invalidate.call_args[0][1]
    assert user_id_arg == 42, "Token invalidation must target user_id=42."


async def test_otp_request_does_not_store_token_for_unknown_user(client: AsyncClient) -> None:
    """No DB write occurs when the email address is not registered."""
    with (
        patch("db.auth.get_user_by_email", return_value=None),
        patch("db.auth.add_otp_token") as mock_save,
    ):
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "nobody@tul.cz"},
        )

    mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# OTP hashing (unit-level, no HTTP)
# ---------------------------------------------------------------------------


def test_hash_otp_produces_bcrypt_hash() -> None:
    """_hash_otp must return a string that bcrypt can verify against the original value."""
    from services.auth_service import _hash_otp

    otp = "123456"
    hashed = _hash_otp(otp)
    assert bcrypt.checkpw(otp.encode(), hashed.encode())


def test_hash_otp_produces_unique_hashes() -> None:
    """Each call to _hash_otp must use a fresh salt, producing a different hash."""
    from services.auth_service import _hash_otp

    otp = "654321"
    assert _hash_otp(otp) != _hash_otp(otp)


def test_generate_otp_is_six_digits() -> None:
    """_generate_otp must return a string of exactly 6 numeric characters."""
    from services.auth_service import _generate_otp

    otp = _generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


async def test_otp_request_response_schema(client: AsyncClient) -> None:
    """The 200 response body must contain only a 'message' key."""
    with patch("db.auth.get_user_by_email", return_value=None):
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "anyone@tul.cz"},
        )
    assert response.status_code == 200
    assert set(response.json().keys()) == {"message"}
