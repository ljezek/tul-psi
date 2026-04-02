from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType


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
    submitted_at: datetime


class CourseEvaluationDetail(BaseModel):
    """Student course evaluation, visible to lecturers/admins when results are unlocked."""

    id: int
    student_id: int
    rating: int
    strengths: str | None
    improvements: str | None
    published: bool
    submitted_at: datetime


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


class ProjectCreate(BaseModel):
    """Input schema for creating a new project.

    ``owner_email`` is optional; when provided the system looks up (or creates)
    the student account and seeds an initial project member, faking an invite email.
    """

    title: str
    description: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    technologies: list[str] = []
    academic_year: int
    # Optional email of the student who owns this project.
    owner_email: str | None = None


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
