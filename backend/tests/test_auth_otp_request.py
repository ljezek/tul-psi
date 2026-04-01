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


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a mock SQLModel session with no user found by default."""
    mock = MagicMock(spec=Session)
    mock.exec.return_value.first.return_value = None
    return mock


@pytest.fixture(autouse=True)
def _override_session(mock_session: MagicMock) -> Generator[None, None, None]:
    """Override the get_session dependency for every test in this module.

    Individual tests that need to control the DB result can accept the
    ``mock_session`` fixture as a parameter and set attributes on it.
    """

    def override() -> Generator[MagicMock, None, None]:
        yield mock_session

    app.dependency_overrides[get_session] = override
    yield
    app.dependency_overrides.pop(get_session, None)


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
    # mock_session already returns None from .first() by default.
    response = await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "unknown@tul.cz"},
    )
    assert response.status_code == 200
    assert "OTP" in response.json()["message"]


async def test_otp_request_returns_200_for_registered_email(
    client: AsyncClient, mock_session: MagicMock
) -> None:
    """Returns HTTP 200 when a matching user is found and the OTP is stored."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_session.exec.return_value.first.return_value = mock_user

    response = await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "jan.novak@tul.cz"},
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# OTP storage (unit-level)
# ---------------------------------------------------------------------------


async def test_otp_request_stores_token_for_registered_user(
    client: AsyncClient, mock_session: MagicMock
) -> None:
    """The stored OtpToken has the correct user_id, timestamps, and a valid bcrypt hash."""
    mock_user = MagicMock()
    mock_user.id = 42
    mock_session.exec.return_value.first.return_value = mock_user

    known_otp = "483921"
    with patch("services.auth_service._generate_otp", return_value=known_otp):
        before = datetime.now(UTC)
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "jan.novak@tul.cz"},
        )
        after = datetime.now(UTC)

    # Find the OtpToken instance that was passed to session.add().
    added = [c[0][0] for c in mock_session.add.call_args_list]
    tokens = [obj for obj in added if isinstance(obj, OtpToken)]
    assert len(tokens) == 1, "Exactly one new OtpToken should have been persisted."
    token = tokens[0]

    assert token.user_id == 42
    assert before <= token.created_at <= after + timedelta(seconds=1)
    assert (
        timedelta(minutes=14, seconds=59)
        <= (token.expires_at - token.created_at)
        <= timedelta(minutes=15, seconds=1)
    )
    assert bcrypt.checkpw(known_otp.encode(), token.token_hash.encode())


async def test_otp_request_invalidates_old_tokens_for_user(
    client: AsyncClient, mock_session: MagicMock
) -> None:
    """A new OTP request must issue a bulk UPDATE to invalidate previous active tokens."""
    from sqlalchemy.sql.dml import Update as SAUpdate

    mock_user = MagicMock()
    mock_user.id = 42
    mock_session.exec.return_value.first.return_value = mock_user

    await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "jan.novak@tul.cz"},
    )

    exec_stmts = [call.args[0] for call in mock_session.exec.call_args_list if call.args]
    updates = [s for s in exec_stmts if isinstance(s, SAUpdate)]
    assert len(updates) == 1, "Expected exactly one bulk UPDATE for token invalidation."

    stmt = updates[0]
    assert stmt.table.name == "otp_token"
    # Verify the UPDATE targets user_id == 42 via the compiled WHERE clause parameters.
    params = stmt.compile().params
    assert params.get("user_id_1") == 42, "UPDATE must filter by user_id=42."


async def test_otp_request_does_not_store_token_for_unknown_user(
    client: AsyncClient, mock_session: MagicMock
) -> None:
    """No DB write occurs when the email address is not registered."""
    # mock_session already returns None from .first() by default.
    await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "nobody@tul.cz"},
    )

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


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
    response = await client.post(
        "/api/v1/auth/otp/request",
        json={"email": "anyone@tul.cz"},
    )
    assert response.status_code == 200
    assert set(response.json().keys()) == {"message"}
