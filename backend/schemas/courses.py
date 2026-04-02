from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType
from schemas.projects import LecturerPublic


class CourseStats(BaseModel):
    """Aggregated statistics for a course derived from its associated projects."""

    project_count: int
    # Sorted list of distinct academic years in which the course had projects.
    academic_years: list[int]


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
    published: bool
    submitted_at: datetime


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
