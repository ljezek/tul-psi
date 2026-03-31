from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from models import Course, CourseTerm, Project, ProjectMember, ProjectType, User, UserRole

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
    """Course can be instantiated with only the required fields."""
    assert sample_course.code == "PSI"
    assert sample_course.name == "Projektový seminář informatiky"
    assert sample_course.term == CourseTerm.WINTER
    assert sample_course.project_type == ProjectType.TEAM
    assert sample_course.min_score == 50


def test_course_id_defaults_to_none(sample_course: Course) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_course.id is None


def test_course_optional_fields_default_to_none(sample_course: Course) -> None:
    """Nullable fields must default to None when not supplied."""
    assert sample_course.syllabus is None
    assert sample_course.peer_bonus_budget is None
    assert sample_course.created_by is None


def test_course_jsonb_fields_default_to_empty_list(sample_course: Course) -> None:
    """evaluation_criteria and links must default to [] so new instances are valid."""
    assert sample_course.evaluation_criteria == []
    assert sample_course.links == []


def test_course_jsonb_fields_accept_structured_data() -> None:
    """evaluation_criteria and links must accept their expected JSONB element shapes."""
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


def test_course_evaluation_criteria_rejects_missing_keys() -> None:
    """evaluation_criteria items missing required keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD",
            name="Bad Course",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            # missing 'description' and 'max_score'
            evaluation_criteria=[{"code": "x"}],
        )


def test_course_evaluation_criteria_rejects_extra_keys() -> None:
    """evaluation_criteria items with unexpected extra keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD3",
            name="Bad Course 3",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            evaluation_criteria=[
                {"code": "x", "description": "X", "max_score": 10, "unknown_field": "nope"}
            ],
        )


def test_course_links_rejects_missing_keys() -> None:
    """links items missing required keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD2",
            name="Bad Course 2",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            # missing 'url'
            links=[{"label": "only label"}],
        )


def test_course_links_rejects_extra_keys() -> None:
    """links items with unexpected extra keys must raise a validation error."""
    with pytest.raises(ValidationError):
        Course(
            code="BAD4",
            name="Bad Course 4",
            term=CourseTerm.WINTER,
            project_type=ProjectType.TEAM,
            min_score=50,
            links=[
                {"label": "eLearning", "url": "https://elearning.tul.cz/", "unknown_field": "nope"}
            ],
        )


def test_course_created_at_defaults_to_now() -> None:
    """created_at must be set to the current UTC time on instantiation."""
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


def test_course_is_registered_in_metadata() -> None:
    """Course table must be present in SQLModel.metadata after import."""
    assert "course" in SQLModel.metadata.tables


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
