from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from models import ProjectMember

# ---------------------------------------------------------------------------
# ProjectMember model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_member() -> ProjectMember:
    return ProjectMember(project_id=1, user_id=2)


def test_project_member_create_minimal(sample_member: ProjectMember) -> None:
    """ProjectMember can be instantiated with only project_id and user_id."""
    assert sample_member.project_id == 1
    assert sample_member.user_id == 2


def test_project_member_id_defaults_to_none(sample_member: ProjectMember) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_member.id is None


def test_project_member_invited_by_defaults_to_none(sample_member: ProjectMember) -> None:
    """invited_by is None when the project owner was seeded directly."""
    assert sample_member.invited_by is None


def test_project_member_joined_at_defaults_to_none(sample_member: ProjectMember) -> None:
    """joined_at is None until the invitation is accepted."""
    assert sample_member.joined_at is None


def test_project_member_invited_at_defaults_to_now(sample_member: ProjectMember) -> None:
    """invited_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    member = ProjectMember(project_id=1, user_id=2)
    after = datetime.now(UTC)
    assert before <= member.invited_at <= after


def test_project_member_is_registered_in_metadata() -> None:
    """project_member table must be present in SQLModel.metadata after import."""
    assert "project_member" in SQLModel.metadata.tables


def test_project_member_rejects_duplicate_membership() -> None:
    """Inserting the same (project_id, user_id) pair twice must raise an IntegrityError."""
    engine = create_engine("sqlite:///:memory:")
    # Create only the project_member table; FK enforcement is off by default in SQLite.
    SQLModel.metadata.tables["project_member"].create(engine)
    with Session(engine) as session:
        session.add(ProjectMember(project_id=1, user_id=1))
        session.commit()
        session.add(ProjectMember(project_id=1, user_id=1))
        with pytest.raises(IntegrityError):
            session.commit()
