from __future__ import annotations

from pydantic import BaseModel

from models.course import CourseTerm


class CoursePublic(BaseModel):
    """Public representation of a course embedded in a project response."""

    id: int
    code: str
    name: str
    term: CourseTerm


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
