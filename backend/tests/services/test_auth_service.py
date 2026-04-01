from __future__ import annotations

import bcrypt

from services.auth_service import _generate_otp, _hash_otp

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
