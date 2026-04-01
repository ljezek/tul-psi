from __future__ import annotations

import pytest
from sqlmodel import SQLModel

from models import Project

# ---------------------------------------------------------------------------
# Project model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_project() -> Project:
    return Project(title="SPC", course_id=1, academic_year=2025)


def test_project_create_minimal(sample_project: Project) -> None:
    """Project can be instantiated with only the required fields."""
    assert sample_project.title == "SPC"
    assert sample_project.course_id == 1
    assert sample_project.academic_year == 2025


def test_project_id_defaults_to_none(sample_project: Project) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_project.id is None


def test_project_optional_fields_default_to_none(sample_project: Project) -> None:
    """Nullable URL/description fields must default to None when not supplied."""
    assert sample_project.description is None
    assert sample_project.github_url is None
    assert sample_project.live_url is None


def test_project_results_unlocked_defaults_to_false(sample_project: Project) -> None:
    """results_unlocked must default to False — results are hidden until unlocked by a lecturer."""
    assert sample_project.results_unlocked is False


def test_project_technologies_defaults_to_empty_list(sample_project: Project) -> None:
    """technologies JSONB array must default to [] when not supplied."""
    assert sample_project.technologies == []


def test_project_technologies_accept_string_list() -> None:
    """technologies must accept a list of technology name strings."""
    project = Project(
        title="SPC",
        course_id=1,
        academic_year=2025,
        technologies=["Python", "FastAPI", "React"],
    )
    assert project.technologies == ["Python", "FastAPI", "React"]


def test_project_is_registered_in_metadata() -> None:
    """Project table must be present in SQLModel.metadata after import."""
    assert "project" in SQLModel.metadata.tables
