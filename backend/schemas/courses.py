from __future__ import annotations

from pydantic import BaseModel

from models.course import CourseLink, CourseTerm, EvaluationCriterion, ProjectType
from schemas.projects import LecturerPublic


class CourseStats(BaseModel):
    """Aggregated statistics for a course derived from its associated projects."""

    project_count: int
    # Sorted list of distinct academic years in which the course had projects.
    academic_years: list[int]
    # Sorted list of lecturer names assigned to the course.
    lecturer_names: list[str]


class CourseListItem(BaseModel):
    """Minimal public representation of a course returned by the list endpoint.

    Only code, name, and aggregated stats are included; full structured fields
    (evaluation_criteria, links, etc.) are reserved for the detail endpoint.
    """

    id: int
    code: str
    name: str
    stats: CourseStats


class CourseDetail(BaseModel):
    """Full public representation of a single course.

    All fields here are visible to unauthenticated users. Sensitive information
    (e.g. individual student data) is never included.
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
