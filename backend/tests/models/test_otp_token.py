from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import SQLModel

from models import OtpToken

# ---------------------------------------------------------------------------
# OtpToken model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_otp_token() -> OtpToken:
    return OtpToken(user_id=1, token_hash="abc123hash")  # noqa: S106


def test_otp_token_create_minimal(sample_otp_token: OtpToken) -> None:
    """OtpToken can be instantiated with only user_id and token_hash."""
    assert sample_otp_token.user_id == 1
    assert sample_otp_token.token_hash == "abc123hash"  # noqa: S105


def test_otp_token_default_fields(sample_otp_token: OtpToken) -> None:
    """id, attempts, and used must default correctly on a new token."""
    assert sample_otp_token.id is None
    assert sample_otp_token.attempts == 0
    assert sample_otp_token.used is False


def test_otp_token_expires_at_defaults_to_15_minutes() -> None:
    """expires_at must default to approximately 15 minutes from the creation time."""
    before = datetime.now(UTC)
    token = OtpToken(user_id=1, token_hash="somehash")  # noqa: S106
    after = datetime.now(UTC)
    assert before + timedelta(minutes=15) <= token.expires_at <= after + timedelta(minutes=15)


def test_otp_token_created_at_defaults_to_now() -> None:
    """created_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    token = OtpToken(user_id=1, token_hash="somehash")  # noqa: S106
    after = datetime.now(UTC)
    assert before <= token.created_at <= after


def test_otp_token_is_registered_in_metadata() -> None:
    """otp_token table must be present in SQLModel.metadata after import."""
    assert "otp_token" in SQLModel.metadata.tables
