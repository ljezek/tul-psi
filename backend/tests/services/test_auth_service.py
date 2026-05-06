from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.auth_service import (
    IncorrectOtpError,
    _generate_otp,
    _hash_otp,
    request_otp,
    verify_otp,
)

# ---------------------------------------------------------------------------
# OTP hashing (unit-level, no HTTP)
# ---------------------------------------------------------------------------


def test_hash_otp_produces_bcrypt_hash() -> None:
    """_hash_otp must return a string that bcrypt can verify against the original value."""
    otp = "123456"
    hashed = _hash_otp(otp)
    assert bcrypt.checkpw(otp.encode(), hashed.encode())


def test_hash_otp_produces_unique_hashes() -> None:
    """Each call to _hash_otp must use a fresh salt, producing a different hash."""
    otp = "654321"
    assert _hash_otp(otp) != _hash_otp(otp)


def test_generate_otp_is_six_digits() -> None:
    """_generate_otp must return a string of exactly 6 numeric characters."""
    otp = _generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


@pytest.mark.asyncio
async def test_request_otp_for_inactive_user() -> None:
    """request_otp must return early if the user is found but marked as inactive."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_user = MagicMock(spec=User)
    mock_user.is_active = False

    with (
        patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user),
        patch("db.auth.add_otp_token") as mock_add_token,
    ):
        await request_otp("test@tul.cz", mock_session)

    mock_add_token.assert_not_called()


@pytest.mark.asyncio
async def test_verify_otp_for_inactive_user() -> None:
    """verify_otp must raise IncorrectOtpError if the user is found but marked as inactive."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_user = MagicMock(spec=User)
    mock_user.is_active = False

    with patch("db.auth.get_user_by_email", new_callable=AsyncMock, return_value=mock_user):
        with pytest.raises(IncorrectOtpError):
            await verify_otp("test@tul.cz", "123456", mock_session)
