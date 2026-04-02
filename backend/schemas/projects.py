from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType
from validators import validate_tul_email


class LecturerPublic(BaseModel):
    """Representation of a lecturer assigned to a course.

    ``email`` is ``None`` for unauthenticated users and populated for authenticated ones.
    """

    name: str
    github_alias: str | None
    # Null for unauthenticated users — email is only visible to authenticated callers.
    email: str | None = None


class CoursePublic(BaseModel):
    """Representation of a course embedded in a project response.

    All non-email fields are visible to unauthenticated users. ``code`` is the natural
    unique identifier for a course and replaces an integer ``id`` for lookups.
    """

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


class MemberPublic(BaseModel):
    """Representation of a project team member.

    ``email`` is ``None`` for unauthenticated users and populated for authenticated ones.
    """

    id: int
    github_alias: str | None
    name: str
    # Null for unauthenticated users — email is only visible to authenticated callers.
    email: str | None = None


class EvaluationScoreDetail(BaseModel):
    """Single per-criterion score within a ``ProjectEvaluationDetail``."""

    criterion_code: str
    score: int
    strengths: str
    improvements: str


class ProjectEvaluationDetail(BaseModel):
    """Lecturer evaluation of the project, visible when results are unlocked."""

    lecturer_id: int
    scores: list[EvaluationScoreDetail]
    updated_at: datetime
    submitted: bool


class CourseEvaluationDetail(BaseModel):
    """Student course evaluation, visible to lecturers/admins when results are unlocked."""

    id: int
    student_id: int
    rating: int
    strengths: str | None
    improvements: str | None
    submitted: bool
    updated_at: datetime


class PeerFeedbackDetail(BaseModel):
    """Peer feedback entry visible based on role when results are unlocked.

    Students see only feedback *received by* them or *written by* them.
    Lecturers and admins see all peer feedback via the course evaluations.
    """

    course_evaluation_id: int
    receiving_student_id: int
    strengths: str | None
    improvements: str | None
    bonus_points: int


class ProjectEvaluationCreate(BaseModel):
    """Request body for ``POST /projects/{id}/project-evaluation``.

    ``submitted=False`` saves the evaluation as a draft that can be updated later.
    ``submitted=True`` marks the evaluation as final and triggers the automatic
    project-result unlock check once all lecturers and students have submitted.

    ``EvaluationScoreDetail`` is reused for the per-criterion entries because the
    fields needed when creating a score are identical to those returned in the detail
    response (criterion_code, score, strengths, improvements).
    """

    scores: list[EvaluationScoreDetail]
    # False means save as draft; True means finalise and trigger auto-unlock.
    submitted: bool = False


class ProjectCreate(BaseModel):
    """Input schema for creating a new project.

    ``owner_email`` is optional; when provided the system looks up (or creates)
    the student account and seeds an initial project member, faking an invite email.
    """

    title: str
    description: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    technologies: list[str] = Field(default_factory=list)
    academic_year: int
    # Optional email of the student who owns this project.
    owner_email: EmailStr | None = None

    @field_validator("owner_email")
    @classmethod
    def owner_email_must_be_tul_domain(cls, v: str | None) -> str | None:
        """Reject any address whose domain is not @tul.cz."""
        if v is None:
            return v
        return validate_tul_email(v)


class ProjectUpdate(BaseModel):
    """Request body for ``PATCH /projects/{id}``.

    All fields are optional. Only fields provided with a non-null value will be updated.
    Passing ``None`` is currently equivalent to omitting the field and does not clear it.
    """

    title: str | None = None
    description: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    technologies: list[str] | None = None


class AddUserBody(BaseModel):
    """Request body for adding a user (student or lecturer) to a resource.

    ``name`` and ``github_alias`` are propagated to a newly-created user account
    when no existing user matches the given *email*.  When omitted, ``github_alias``
    defaults to ``None`` and ``name`` defaults to the local part of the e-mail
    address (the portion before the ``@`` sign).
    """

    email: EmailStr
    name: str | None = None
    github_alias: str | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_tul_domain(cls, v: str) -> str:
        """Reject any address whose domain is not @tul.cz."""
        return validate_tul_email(v)


# Backward-compatible alias used in project-member endpoints.
AddMemberBody = AddUserBody


class ProjectPublic(BaseModel):
    """Project representation returned to all callers.

    For unauthenticated requests, private fields (``results_unlocked``,
    ``course.lecturers[*].email``, ``members[*].email``, and all evaluation
    collections) are ``None``.  Authenticated callers receive those fields
    populated according to their role.
    """

    id: int
    title: str
    description: str | None
    github_url: str | None
    live_url: str | None
    technologies: list[str]
    academic_year: int
    course: CoursePublic
    members: list[MemberPublic]
    # Null for unauthenticated users.
    results_unlocked: bool | None = None
    # Populated for all roles when results_unlocked is True.
    project_evaluations: list[ProjectEvaluationDetail] | None = None
    # Populated for lecturer/admin when results_unlocked is True.
    course_evaluations: list[CourseEvaluationDetail] | None = None
    # Populated for student when results_unlocked is True.
    received_peer_feedback: list[PeerFeedbackDetail] | None = None
    # Populated for student when results_unlocked is True.
    authored_peer_feedback: list[PeerFeedbackDetail] | None = None


class PeerFeedbackInput(BaseModel):
    """A single peer feedback entry submitted as part of a course evaluation.

    ``receiving_student_id`` must reference a project teammate (validated at
    the service layer).  ``bonus_points`` is zero when the course does not
    use a peer-bonus scheme; the service validates that the total across all
    entries equals ``Course.peer_bonus_budget`` on final submission.
    """

    receiving_student_id: int
    strengths: str | None = None
    improvements: str | None = None
    # Zero when the course has no peer-bonus scheme.
    bonus_points: int = 0


class CourseEvaluationUpsert(BaseModel):
    """Request body for ``PUT /projects/{id}/course-evaluation``.

    ``submitted=False`` (default) saves the evaluation as a draft that can be
    updated later.  ``submitted=True`` finalises the evaluation and triggers
    the automatic project-result unlock check once all students and lecturers
    have submitted.
    """

    # Overall course satisfaction rating; must be in the 1–5 range.
    rating: int
    strengths: str | None = None
    improvements: str | None = None
    # False means save as draft; True means finalise and trigger auto-unlock.
    submitted: bool = False
    peer_feedback: list[PeerFeedbackInput] = Field(default_factory=list)

    @field_validator("rating")
    @classmethod
    def rating_must_be_in_range(cls, v: int) -> int:
        """Reject any rating outside the 1–5 scale."""
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5.")
        return v


class CourseEvaluationFormResponse(BaseModel):
    """Response for ``GET /projects/{id}/course-evaluation``.

    Returns all data a student needs to render and populate the combined
    course-evaluation and peer-feedback form.  When ``results_unlocked`` is
    ``True`` the form is read-only and the evaluation can no longer be edited.
    """

    # Project members other than the requesting student.
    teammates: list[MemberPublic]
    # Null when the course has no peer-bonus scheme.
    peer_bonus_budget: int | None
    # Null when the student has not yet started a draft.
    current_evaluation: CourseEvaluationDetail | None
    # One entry per teammate; empty list when no draft exists yet.
    authored_peer_feedback: list[PeerFeedbackDetail]
    results_unlocked: bool
