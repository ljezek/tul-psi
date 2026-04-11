from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType
from schemas.projects import LecturerPublic


class CourseStats(BaseModel):
    """Aggregated statistics for a course derived from its associated projects."""

    project_count: int
    # Sorted list of distinct academic years in which the course had projects.
    academic_years: list[int]
    # Number of projects in the course that the current lecturer has not yet evaluated.
    pending_evaluations_count: int | None = None


class CourseListItem(BaseModel):
    """Minimal public representation of a course returned by the list endpoint.

    Includes the course code, name, syllabus, sorted lecturer names, and
    aggregated project stats.  Full structured fields (evaluation_criteria,
    links, etc.) are reserved for the detail endpoint.
    """

    id: int
    code: str
    name: str
    syllabus: str | None
    # Sorted list of names of lecturers assigned to the course.
    lecturer_names: list[str]
    stats: CourseStats


class CourseEvaluationPublic(BaseModel):
    """Public representation of a student course evaluation.

    Only exposed to authenticated admin users and to lecturers who own the
    course.  Contains evaluations from projects whose ``results_unlocked``
    flag is set, so that the data is visible to students before it is
    surfaced here to lecturers.
    """

    id: int
    project_id: int
    student_id: int
    rating: int
    strengths: str | None
    improvements: str | None
    submitted: bool
    updated_at: datetime


class CourseDetail(BaseModel):
    """Full public representation of a single course.

    All base fields are visible to unauthenticated users.  The
    ``course_evaluations`` field is populated only for admin users and for
    lecturers assigned to the course; it is ``None`` otherwise.
    """

    id: int
    code: str
    name: str
    syllabus: str | None
    term: CourseTerm
    project_type: ProjectType
    min_score: int
    # Null means no peer-bonus-point scheme for this course.
    peer_bonus_budget: int | None
    evaluation_criteria: list[EvaluationCriterion]
    links: list[CourseLink]
    lecturers: list[LecturerPublic]
    # Null for unauthenticated users and for roles without course access.
    course_evaluations: list[CourseEvaluationPublic] | None = None


class CourseCreate(BaseModel):
    """Request body for creating a new course.

    Only admins may create courses.  The ``code`` must be unique across all
    courses.  Optional structured fields default to empty lists so that the
    minimal creation payload is just ``code``, ``name``, ``term``,
    ``project_type``, and ``min_score``.
    """

    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    term: CourseTerm
    project_type: ProjectType
    min_score: int
    owner_email: EmailStr
    syllabus: str | None = None
    # Null means no peer-bonus-point scheme for this course.
    peer_bonus_budget: int | None = None
    evaluation_criteria: list[EvaluationCriterion] = Field(default_factory=list)
    links: list[CourseLink] = Field(default_factory=list)


class CourseUpdate(BaseModel):
    """Request body for a partial course update (PATCH).

    Only fields present in the request body are updated; omitted fields are
    left unchanged.  ``syllabus`` can be set to ``null`` to clear it.
    ``peer_bonus_budget`` can be set to ``null`` to disable the peer-bonus
    scheme.  The JSONB list fields ``evaluation_criteria`` and ``links`` cannot
    be set to ``null`` — omit them to leave them unchanged.
    """

    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    term: CourseTerm | None = None
    project_type: ProjectType | None = None
    min_score: int | None = None
    # Setting to null clears the syllabus.
    syllabus: str | None = None
    # Setting to null disables the peer-bonus scheme.
    peer_bonus_budget: int | None = None
    evaluation_criteria: list[EvaluationCriterion] | None = None
    links: list[CourseLink] | None = None

    @model_validator(mode="after")
    def _non_nullable_list_fields_not_null(self) -> CourseUpdate:
        """Reject explicit null for JSONB list fields that are non-nullable in the DB."""
        for field in ("evaluation_criteria", "links"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' may not be null; provide a list or omit the field.")
        return self


class CourseLecturerPublic(BaseModel):
    """Representation of a lecturer assigned to a course, returned by management endpoints.

    Includes the ``id`` field (the user's primary key) so that callers can
    reference the lecturer in subsequent operations such as DELETE.
    """

    id: int
    name: str
    github_alias: str | None
    email: str


class CriterionScoreSummary(BaseModel):
    """Per-criterion score with verbatim text feedback from a single lecturer evaluation."""

    criterion_code: str
    score: int
    # Verbatim text feedback written by the lecturer for this criterion; nullable
    # because the source data may not always include both fields.
    strengths: str | None
    improvements: str | None


class ProjectEvaluationSummary(BaseModel):
    """All criterion scores submitted by a single lecturer for a project."""

    lecturer_id: int
    criterion_scores: list[CriterionScoreSummary]


class CourseEvaluationSummary(BaseModel):
    """Anonymous student course evaluation for the overview endpoint.

    Student identity is not exposed in the overview; only the rating and
    optional text fields are included so that lecturers can read the verbatim
    feedback without identifying individual students.
    """

    # Null when the student has not provided a rating (drafts or legacy rows).
    rating: int | None
    strengths: str | None
    improvements: str | None


class ReceivedPeerFeedback(BaseModel):
    """Anonymous peer feedback received by one student from a single teammate.

    The giver's identity is not exposed so that the feedback remains
    pseudonymous from the receiving student's perspective.
    """

    bonus_points: int
    strengths: str | None
    improvements: str | None


class StudentBonusSummary(BaseModel):
    """All peer feedback received by a single student within a project.

    Each entry in ``feedback`` represents one teammate's submission.  The
    frontend computes any desired aggregations (e.g. average bonus) from the
    individual entries.
    """

    student_id: int
    student_name: str
    feedback: list[ReceivedPeerFeedback]


class ProjectOverviewItem(BaseModel):
    """Full evaluation data for a single project in the overview.

    ``project_evaluations`` is empty when no lecturers have submitted evaluations.
    ``course_evaluations`` is empty when no students have submitted course evaluations.
    ``student_bonus_points`` is empty when the course has no peer-bonus scheme or
    no peer feedback has been submitted yet.  The frontend is responsible for
    computing any desired aggregations (averages, totals, etc.) from the raw entries.
    """

    project_id: int
    project_title: str
    academic_year: int
    # One entry per submitted lecturer evaluation.
    project_evaluations: list[ProjectEvaluationSummary]
    # One entry per submitted student course evaluation (anonymous — no student_id).
    course_evaluations: list[CourseEvaluationSummary]
    # One entry per receiving student; each contains all peer feedback items for that student.
    student_bonus_points: list[StudentBonusSummary]


class EvaluationOverviewResponse(BaseModel):
    """Evaluation overview for all projects in a course.

    Sorted by ``academic_year`` descending and then ``project_title`` ascending,
    matching the ordering applied at the DB query layer.
    """

    projects: list[ProjectOverviewItem]
