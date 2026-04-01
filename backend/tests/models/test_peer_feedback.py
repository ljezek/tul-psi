from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from models import PeerFeedback

# ---------------------------------------------------------------------------
# PeerFeedback model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_peer_feedback() -> PeerFeedback:
    return PeerFeedback(course_evaluation_id=1, receiving_student_id=4)


def test_peer_feedback_create_minimal(sample_peer_feedback: PeerFeedback) -> None:
    """PeerFeedback can be instantiated with only course_evaluation_id and receiving_student_id."""
    assert sample_peer_feedback.course_evaluation_id == 1
    assert sample_peer_feedback.receiving_student_id == 4


def test_peer_feedback_default_fields(sample_peer_feedback: PeerFeedback) -> None:
    """strengths, improvements, and bonus_points must default correctly on a new instance."""
    assert sample_peer_feedback.strengths is None
    assert sample_peer_feedback.improvements is None
    assert sample_peer_feedback.bonus_points == 0


def test_peer_feedback_is_registered_in_metadata() -> None:
    """peer_feedback table must be present in SQLModel.metadata after import."""
    assert "peer_feedback" in SQLModel.metadata.tables


def test_peer_feedback_rejects_duplicate_feedback() -> None:
    """Inserting the same (course_evaluation_id, receiving_student_id) pair twice
    must raise an IntegrityError.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.tables["peer_feedback"].create(engine)
    with Session(engine) as session:
        session.add(PeerFeedback(course_evaluation_id=1, receiving_student_id=2))
        session.commit()
        session.add(PeerFeedback(course_evaluation_id=1, receiving_student_id=2))
        with pytest.raises(IntegrityError):
            session.commit()
