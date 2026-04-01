from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import SQLModel

from models import User, UserRole

# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


def test_user_create_minimal() -> None:
    """User can be instantiated with only the required fields."""
    user = User(email="alice@example.com", name="Alice", role=UserRole.STUDENT)
    assert user.email == "alice@example.com"
    assert user.name == "Alice"
    assert user.role == UserRole.STUDENT


def test_user_id_defaults_to_none() -> None:
    """id must be None before the record is persisted to the database."""
    user = User(email="bob@example.com", name="Bob", role=UserRole.LECTURER)
    assert user.id is None


def test_user_github_alias_defaults_to_none() -> None:
    """github_alias is optional and must default to None when not supplied."""
    user = User(email="carol@example.com", name="Carol", role=UserRole.ADMIN)
    assert user.github_alias is None


def test_user_created_at_defaults_to_now() -> None:
    """created_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    user = User(email="dave@example.com", name="Dave", role=UserRole.STUDENT)
    after = datetime.now(UTC)
    assert before <= user.created_at <= after


def test_user_is_registered_in_metadata() -> None:
    """User table must be present in SQLModel.metadata after import."""
    assert "user" in SQLModel.metadata.tables
