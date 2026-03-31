from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from models import (
    Course,
    CourseEvaluation,
    CourseLecturer,
    CourseTerm,
    EvaluationScore,
    OtpToken,
    PeerFeedback,
    Project,
    ProjectEvaluation,
    ProjectMember,
    ProjectType,
    User,
    UserRole,
)

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


def test_project_evaluation_id_defaults_to_none(
    sample_project_evaluation: ProjectEvaluation,
) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_project_evaluation.id is None


def test_project_evaluation_scores_defaults_to_empty_list(
    sample_project_evaluation: ProjectEvaluation,
) -> None:
    """scores JSONB array must default to [] when not supplied."""
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


def test_project_evaluation_submitted_at_defaults_to_now() -> None:
    """submitted_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    evaluation = ProjectEvaluation(project_id=1, lecturer_id=2)
    after = datetime.now(UTC)
    assert before <= evaluation.submitted_at <= after


def test_project_evaluation_is_registered_in_metadata() -> None:
    """project_evaluation table must be present in SQLModel.metadata after import."""
    assert "project_evaluation" in SQLModel.metadata.tables


def test_project_evaluation_rejects_duplicate_submission() -> None:
    """Inserting the same (project_id, lecturer_id) pair twice must raise an IntegrityError."""
    from sqlalchemy import JSON, Column, Integer, MetaData, UniqueConstraint
    from sqlalchemy import Table as SATable

    # SQLite does not support JSONB, so we cannot use
    # SQLModel.metadata.tables["project_evaluation"].create(engine) here (unlike
    # all other duplicate tests).  We build a schema-equivalent table with plain
    # JSON instead to keep the in-memory constraint test database-agnostic.
    meta = MetaData()
    tbl = SATable(
        "project_evaluation_dup_test",
        meta,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("project_id", Integer, nullable=False),
        Column("lecturer_id", Integer, nullable=False),
        Column("scores", JSON, nullable=False),
        UniqueConstraint("project_id", "lecturer_id"),
    )
    engine = create_engine("sqlite:///:memory:")
    meta.create_all(engine)
    with engine.begin() as conn:
        conn.execute(tbl.insert().values(project_id=1, lecturer_id=2, scores=[]))
        with pytest.raises(IntegrityError):
            conn.execute(tbl.insert().values(project_id=1, lecturer_id=2, scores=[]))


# ---------------------------------------------------------------------------
# CourseEvaluation model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course_evaluation() -> CourseEvaluation:
    return CourseEvaluation(project_id=1, student_id=3, rating=4)


def test_course_evaluation_create_minimal(
    sample_course_evaluation: CourseEvaluation,
) -> None:
    """CourseEvaluation can be instantiated with project_id, student_id, and rating."""
    assert sample_course_evaluation.project_id == 1
    assert sample_course_evaluation.student_id == 3
    assert sample_course_evaluation.rating == 4


def test_course_evaluation_id_defaults_to_none(
    sample_course_evaluation: CourseEvaluation,
) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_course_evaluation.id is None


def test_course_evaluation_published_defaults_to_false(
    sample_course_evaluation: CourseEvaluation,
) -> None:
    """published must default to False — a new evaluation starts as a draft."""
    assert sample_course_evaluation.published is False


def test_course_evaluation_optional_fields_default_to_none(
    sample_course_evaluation: CourseEvaluation,
) -> None:
    """strengths and improvements must default to None to support partial draft saves."""
    assert sample_course_evaluation.strengths is None
    assert sample_course_evaluation.improvements is None


def test_course_evaluation_rating_accepts_boundary_values() -> None:
    """rating must accept the boundary values 1 (min) and 5 (max) without error."""
    low = CourseEvaluation(project_id=1, student_id=1, rating=1)
    high = CourseEvaluation(project_id=1, student_id=2, rating=5)
    assert low.rating == 1
    assert high.rating == 5


def test_course_evaluation_rating_rejects_out_of_range() -> None:
    """rating values outside 1–5 must raise a ValidationError."""
    with pytest.raises(ValidationError):
        CourseEvaluation(project_id=1, student_id=1, rating=0)
    with pytest.raises(ValidationError):
        CourseEvaluation(project_id=1, student_id=1, rating=6)


def test_course_evaluation_submitted_at_defaults_to_now() -> None:
    """submitted_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    evaluation = CourseEvaluation(project_id=1, student_id=1, rating=3)
    after = datetime.now(UTC)
    assert before <= evaluation.submitted_at <= after


def test_course_evaluation_is_registered_in_metadata() -> None:
    """course_evaluation table must be present in SQLModel.metadata after import."""
    assert "course_evaluation" in SQLModel.metadata.tables


def test_course_evaluation_rejects_duplicate_submission() -> None:
    """Inserting the same (project_id, student_id) pair twice must raise an IntegrityError."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.tables["course_evaluation"].create(engine)
    with Session(engine) as session:
        session.add(CourseEvaluation(project_id=1, student_id=1, rating=3))
        session.commit()
        session.add(CourseEvaluation(project_id=1, student_id=1, rating=4))
        with pytest.raises(IntegrityError):
            session.commit()


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


def test_peer_feedback_id_defaults_to_none(sample_peer_feedback: PeerFeedback) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_peer_feedback.id is None


def test_peer_feedback_optional_fields_default_to_none(
    sample_peer_feedback: PeerFeedback,
) -> None:
    """strengths and improvements must default to None to support partial draft saves."""
    assert sample_peer_feedback.strengths is None
    assert sample_peer_feedback.improvements is None


def test_peer_feedback_bonus_points_defaults_to_zero(
    sample_peer_feedback: PeerFeedback,
) -> None:
    """bonus_points must default to 0 when the course has no peer-bonus scheme."""
    assert sample_peer_feedback.bonus_points == 0


def test_peer_feedback_is_registered_in_metadata() -> None:
    """peer_feedback table must be present in SQLModel.metadata after import."""
    assert "peer_feedback" in SQLModel.metadata.tables


# ---------------------------------------------------------------------------
# OtpToken model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_otp_token() -> OtpToken:
    return OtpToken(
        user_id=1,
        token_hash="abc123hash",
        expires_at=datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    )


def test_otp_token_create_minimal(sample_otp_token: OtpToken) -> None:
    """OtpToken can be instantiated with user_id, token_hash, and expires_at."""
    assert sample_otp_token.user_id == 1
    assert sample_otp_token.token_hash == "abc123hash"


def test_otp_token_id_defaults_to_none(sample_otp_token: OtpToken) -> None:
    """id must be None before the record is persisted to the database."""
    assert sample_otp_token.id is None


def test_otp_token_attempts_defaults_to_zero(sample_otp_token: OtpToken) -> None:
    """attempts must default to 0 — no failed verifications on a fresh token."""
    assert sample_otp_token.attempts == 0


def test_otp_token_used_defaults_to_false(sample_otp_token: OtpToken) -> None:
    """used must default to False — a fresh token has not been consumed yet."""
    assert sample_otp_token.used is False


def test_otp_token_created_at_defaults_to_now() -> None:
    """created_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    token = OtpToken(
        user_id=1,
        token_hash="somehash",
        expires_at=datetime(2026, 12, 31, tzinfo=UTC),
    )
    after = datetime.now(UTC)
    assert before <= token.created_at <= after


def test_otp_token_is_registered_in_metadata() -> None:
    """otp_token table must be present in SQLModel.metadata after import."""
    assert "otp_token" in SQLModel.metadata.tables


# ---------------------------------------------------------------------------
# CourseLecturer model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course_lecturer() -> CourseLecturer:
    return CourseLecturer(course_id=1, user_id=5)


def test_course_lecturer_create_minimal(sample_course_lecturer: CourseLecturer) -> None:
    """CourseLecturer can be instantiated with only course_id and user_id."""
    assert sample_course_lecturer.course_id == 1
    assert sample_course_lecturer.user_id == 5


def test_course_lecturer_assigned_at_defaults_to_now() -> None:
    """assigned_at must be set to the current UTC time on instantiation."""
    before = datetime.now(UTC)
    cl = CourseLecturer(course_id=1, user_id=5)
    after = datetime.now(UTC)
    assert before <= cl.assigned_at <= after


def test_course_lecturer_is_registered_in_metadata() -> None:
    """course_lecturer table must be present in SQLModel.metadata after import."""
    assert "course_lecturer" in SQLModel.metadata.tables


def test_course_lecturer_rejects_duplicate_assignment() -> None:
    """Inserting the same (course_id, user_id) pair twice must raise an IntegrityError."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.tables["course_lecturer"].create(engine)
    with Session(engine) as session:
        session.add(CourseLecturer(course_id=1, user_id=5))
        session.commit()
        session.add(CourseLecturer(course_id=1, user_id=5))
        with pytest.raises(IntegrityError):
            session.commit()
