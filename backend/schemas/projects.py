from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType


class LecturerPublic(BaseModel):
    """Public representation of a lecturer assigned to a course.

    E-mail is intentionally omitted — it is not visible to unauthenticated users.
    """

    name: str
    github_alias: str | None


class LecturerDetail(BaseModel):
    """Lecturer representation for authenticated users — e-mail is included."""

    name: str
    github_alias: str | None
    email: str


class CoursePublic(BaseModel):
    """Public representation of a course embedded in a project response.

    All fields here are visible to unauthenticated users. ``code`` is the natural
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


class CourseDetail(BaseModel):
    """Course representation for authenticated users — lecturers include e-mails."""

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
    lecturers: list[LecturerDetail]


class MemberPublic(BaseModel):
    """Public representation of a project team member."""

    id: int
    github_alias: str | None
    name: str


class MemberDetail(BaseModel):
    """Member representation for authenticated users — e-mail is included."""

    id: int
    github_alias: str | None
    name: str
    email: str


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


class ProjectPublic(BaseModel):
    """Public representation of a project returned by the discovery endpoint."""

    id: int
    title: str
    description: str | None
    github_url: str | None
    live_url: str | None
    technologies: list[str]
    academic_year: int
    course: CoursePublic
    members: list[MemberPublic]


class ProjectDetail(BaseModel):
    """Enriched project representation returned to authenticated users.

    Includes member and lecturer e-mails, the ``results_unlocked`` flag, and —
    when results are unlocked — evaluation and peer-feedback data gated by role:

    * **Lecturer / Admin**: ``project_evaluations`` and ``course_evaluations``.
    * **Student**: ``project_evaluations`` (read-only), ``received_peer_feedback``
      (feedback addressed to this student), and ``authored_peer_feedback``
      (feedback this student wrote for teammates).
    """

    id: int
    title: str
    description: str | None
    github_url: str | None
    live_url: str | None
    technologies: list[str]
    academic_year: int
    results_unlocked: bool
    course: CourseDetail
    members: list[MemberDetail]
    # Populated for all roles when results_unlocked is True.
    project_evaluations: list[ProjectEvaluationDetail] | None = None
    # Populated for lecturer/admin when results_unlocked is True.
    course_evaluations: list[CourseEvaluationDetail] | None = None
    # Populated for student when results_unlocked is True.
    received_peer_feedback: list[PeerFeedbackDetail] | None = None
    # Populated for student when results_unlocked is True.
    authored_peer_feedback: list[PeerFeedbackDetail] | None = None
