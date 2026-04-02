from __future__ import annotations

from pydantic import BaseModel

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType


class LecturerPublic(BaseModel):
    """Public representation of a lecturer assigned to a course.

    ``email`` is ``None`` for unauthenticated requests and is populated when the
    caller holds a valid session, regardless of their role.
    """

    name: str
    github_alias: str | None
    # Null for unauthenticated callers; populated when a valid session is present.
    email: str | None = None


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


class MemberPublic(BaseModel):
    """Public representation of a project team member."""

    id: int
    github_alias: str | None
    name: str


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
