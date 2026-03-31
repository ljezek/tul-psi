from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlmodel import SQLModel

from models import Course, CourseTerm, Project, ProjectMember, ProjectType, User, UserRole

# ---------------------------------------------------------------------------
# UserRole enum
# ---------------------------------------------------------------------------


def test_user_role_values() -> None:
    """UserRole must expose the three expected role strings."""
    assert UserRole.ADMIN == "ADMIN"
    assert UserRole.LECTURER == "LECTURER"
    assert UserRole.STUDENT == "STUDENT"


def test_user_role_is_str_enum() -> None:
    """UserRole values must be valid plain strings (for JSON serialisation)."""
    assert isinstance(UserRole.STUDENT, str)


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
    before = datetime.now(UTC)
    user = User(email="dave@example.com", name="Dave", role=UserRole.STUDENT)
    after = datetime.now(UTC)
    assert before <= user.created_at <= after


def test_user_table_name() -> None:
    """The underlying SQL table must be named 'user' to match the design doc."""
    assert User.__tablename__ == "user"


def test_user_is_registered_in_metadata() -> None:
    """User table must be present in SQLModel.metadata after import."""
    assert "user" in SQLModel.metadata.tables


# ---------------------------------------------------------------------------
# CourseTerm / ProjectType enums
# ---------------------------------------------------------------------------


def test_course_term_values() -> None:
    assert CourseTerm.SUMMER == "SUMMER"
    assert CourseTerm.WINTER == "WINTER"


def test_project_type_values() -> None:
    assert ProjectType.TEAM == "TEAM"
    assert ProjectType.INDIVIDUAL == "INDIVIDUAL"


# ---------------------------------------------------------------------------
# Course model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course() -> Course:
    return Course(
        code="PSI",
        name="Projektový seminář informatiky",
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=50,
    )


def test_course_create_minimal(sample_course: Course) -> None:
    assert sample_course.code == "PSI"
    assert sample_course.name == "Projektový seminář informatiky"
    assert sample_course.term == CourseTerm.WINTER
    assert sample_course.project_type == ProjectType.TEAM
    assert sample_course.min_score == 50


def test_course_id_defaults_to_none(sample_course: Course) -> None:
    assert sample_course.id is None


def test_course_optional_fields_default_to_none(sample_course: Course) -> None:
    assert sample_course.syllabus is None
    assert sample_course.peer_bonus_budget is None
    assert sample_course.created_by is None


def test_course_jsonb_fields_default_to_empty_list(sample_course: Course) -> None:
    """evaluation_criteria and links must default to [] so new instances are valid."""
    assert sample_course.evaluation_criteria == []
    assert sample_course.links == []


def test_course_jsonb_fields_accept_structured_data() -> None:
    criteria = [{"code": "code_quality", "description": "Code Quality", "max_score": 25}]
    links = [{"label": "eLearning", "url": "https://elearning.tul.cz/"}]
    course = Course(
        code="PSI2",
        name="Test Course",
        term=CourseTerm.SUMMER,
        project_type=ProjectType.INDIVIDUAL,
        min_score=40,
        evaluation_criteria=criteria,
        links=links,
    )
    assert course.evaluation_criteria == criteria
    assert course.links == links


def test_course_created_at_defaults_to_now(sample_course: Course) -> None:
    before = datetime.now(UTC)
    course = Course(
        code="XYZ",
        name="X",
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=0,
    )
    after = datetime.now(UTC)
    assert before <= course.created_at <= after


def test_course_table_name() -> None:
    assert Course.__tablename__ == "course"


def test_course_is_registered_in_metadata() -> None:
    assert "course" in SQLModel.metadata.tables


# ---------------------------------------------------------------------------
# Project model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_project() -> Project:
    return Project(title="SPC", course_id=1, academic_year=2025)


def test_project_create_minimal(sample_project: Project) -> None:
    assert sample_project.title == "SPC"
    assert sample_project.course_id == 1
    assert sample_project.academic_year == 2025


def test_project_id_defaults_to_none(sample_project: Project) -> None:
    assert sample_project.id is None


def test_project_optional_fields_default_to_none(sample_project: Project) -> None:
    assert sample_project.description is None
    assert sample_project.github_url is None
    assert sample_project.live_url is None


def test_project_results_unlocked_defaults_to_false(sample_project: Project) -> None:
    assert sample_project.results_unlocked is False


def test_project_technologies_defaults_to_empty_list(sample_project: Project) -> None:
    assert sample_project.technologies == []


def test_project_technologies_accept_string_list() -> None:
    project = Project(
        title="SPC",
        course_id=1,
        academic_year=2025,
        technologies=["Python", "FastAPI", "React"],
    )
    assert project.technologies == ["Python", "FastAPI", "React"]


def test_project_table_name() -> None:
    assert Project.__tablename__ == "project"


def test_project_is_registered_in_metadata() -> None:
    assert "project" in SQLModel.metadata.tables


# ---------------------------------------------------------------------------
# ProjectMember model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_member() -> ProjectMember:
    return ProjectMember(project_id=1, user_id=2)


def test_project_member_create_minimal(sample_member: ProjectMember) -> None:
    assert sample_member.project_id == 1
    assert sample_member.user_id == 2


def test_project_member_id_defaults_to_none(sample_member: ProjectMember) -> None:
    assert sample_member.id is None


def test_project_member_invited_by_defaults_to_none(sample_member: ProjectMember) -> None:
    """invited_by is None when the project owner was seeded directly."""
    assert sample_member.invited_by is None


def test_project_member_joined_at_defaults_to_none(sample_member: ProjectMember) -> None:
    """joined_at is None until the invitation is accepted."""
    assert sample_member.joined_at is None


def test_project_member_invited_at_defaults_to_now(sample_member: ProjectMember) -> None:
    before = datetime.now(UTC)
    member = ProjectMember(project_id=1, user_id=2)
    after = datetime.now(UTC)
    assert before <= member.invited_at <= after


def test_project_member_table_name() -> None:
    assert ProjectMember.__tablename__ == "project_member"


def test_project_member_is_registered_in_metadata() -> None:
    assert "project_member" in SQLModel.metadata.tables
