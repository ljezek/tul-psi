from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

from httpx import AsyncClient
from sqlmodel import Session

from db.session import get_session
from main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session_override(user: object | None) -> tuple[MagicMock, Generator]:
    """Return a (mock_session, override_callable) pair.

    *user* is the value returned by ``session.exec(...).first()``.
    """
    mock_session = MagicMock(spec=Session)
    mock_session.exec.return_value.first.return_value = user

    def override() -> Generator[MagicMock, None, None]:
        yield mock_session

    return mock_session, override


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------


async def test_otp_request_rejects_non_tul_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/otp/request must return 422 for non-@tul.cz addresses."""
    _mock_session, override = _make_session_override(None)
    app.dependency_overrides[get_session] = override
    try:
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "student@gmail.com"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 422


async def test_otp_request_rejects_malformed_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/otp/request must return 422 for addresses that are not valid e-mails."""
    _mock_session, override = _make_session_override(None)
    app.dependency_overrides[get_session] = override
    try:
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "not-an-email"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 422


async def test_otp_request_rejects_tul_cz_subdomain(client: AsyncClient) -> None:
    """A subdomain like @sub.tul.cz must not be accepted — only @tul.cz is valid."""
    _mock_session, override = _make_session_override(None)
    app.dependency_overrides[get_session] = override
    try:
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "user@sub.tul.cz"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Silent-success behaviour (registered & unregistered addresses)
# ---------------------------------------------------------------------------


async def test_otp_request_returns_200_for_unknown_email(client: AsyncClient) -> None:
    """Returns HTTP 200 even when no matching user exists (prevents user enumeration)."""
    _mock_session, override = _make_session_override(None)
    app.dependency_overrides[get_session] = override
    try:
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "unknown@tul.cz"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    assert "OTP" in response.json()["message"]


async def test_otp_request_returns_200_for_registered_email(client: AsyncClient) -> None:
    """Returns HTTP 200 when a matching user is found and the OTP is stored."""
    mock_user = MagicMock()
    mock_user.id = 1
    _mock_session, override = _make_session_override(mock_user)
    app.dependency_overrides[get_session] = override
    try:
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "jan.novak@tul.cz"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# OTP storage (unit-level)
# ---------------------------------------------------------------------------


async def test_otp_request_stores_token_for_registered_user(client: AsyncClient) -> None:
    """An OtpToken row is added to the session when the user exists."""
    mock_user = MagicMock()
    mock_user.id = 42
    mock_session, override = _make_session_override(mock_user)
    app.dependency_overrides[get_session] = override
    try:
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "jan.novak@tul.cz"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    # session.add() must have been called once with an OtpToken-like object.
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


async def test_otp_request_does_not_store_token_for_unknown_user(client: AsyncClient) -> None:
    """No DB write occurs when the email address is not registered."""
    mock_session, override = _make_session_override(None)
    app.dependency_overrides[get_session] = override
    try:
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "nobody@tul.cz"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# OTP hashing (unit-level, no HTTP)
# ---------------------------------------------------------------------------


def test_hash_otp_produces_bcrypt_hash() -> None:
    """_hash_otp must return a string that bcrypt can verify against the original value."""
    import bcrypt

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
    _mock_session, override = _make_session_override(None)
    app.dependency_overrides[get_session] = override
    try:
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "anyone@tul.cz"},
        )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    assert set(response.json().keys()) == {"message"}
