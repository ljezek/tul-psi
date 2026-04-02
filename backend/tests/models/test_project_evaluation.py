from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel

from models import ProjectEvaluation

# ---------------------------------------------------------------------------
# ProjectEvaluation model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_project_evaluation() -> ProjectEvaluation:
    return ProjectEvaluation(project_id=1, lecturer_id=2)


def test_project_evaluation_create_minimal(
    sample_project_evaluation: ProjectEvaluation,
) -> None:
    """ProjectEvaluation can be instantiated with only project_id and lecturer_id."""
    assert sample_project_evaluation.project_id == 1
    assert sample_project_evaluation.lecturer_id == 2


def test_project_evaluation_default_fields(
    sample_project_evaluation: ProjectEvaluation,
) -> None:
    """scores must default to an empty list when not supplied."""
    assert sample_project_evaluation.scores == []


def test_project_evaluation_scores_accept_structured_data() -> None:
    """scores must accept a list of well-formed EvaluationScore elements."""
    scores = [
        {
            "criterion_code": "code_quality",
            "score": 22,
            "strengths": "Well-structured codebase",
            "improvements": "Add docstrings to the service layer",
        }
    ]
    evaluation = ProjectEvaluation(project_id=1, lecturer_id=2, scores=scores)
    assert evaluation.scores == scores


def test_project_evaluation_scores_rejects_missing_keys() -> None:
    """scores items missing required keys must raise a ValidationError."""
    with pytest.raises(ValidationError):
        ProjectEvaluation(
            project_id=1,
            lecturer_id=2,
            # Missing 'improvements' and 'strengths'.
            scores=[{"criterion_code": "code_quality", "score": 22}],
        )


def test_project_evaluation_scores_rejects_extra_keys() -> None:
    """scores items with unexpected extra keys must raise a ValidationError."""
    with pytest.raises(ValidationError):
        ProjectEvaluation(
            project_id=1,
            lecturer_id=2,
            scores=[
                {
                    "criterion_code": "code_quality",
                    "score": 22,
                    "strengths": "Good",
                    "improvements": "More docs",
                    "unknown_field": "nope",
                }
            ],
        )


def test_project_evaluation_updated_at_defaults_to_now() -> None:
    """updated_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    evaluation = ProjectEvaluation(project_id=1, lecturer_id=2)
    after = datetime.now(UTC)
    assert before <= evaluation.updated_at <= after


def test_project_evaluation_is_registered_in_metadata() -> None:
    """project_evaluation table must be present in SQLModel.metadata after import."""
    assert "project_evaluation" in SQLModel.metadata.tables
