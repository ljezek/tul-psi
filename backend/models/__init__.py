from __future__ import annotations

from .course import Course, CourseLink, CourseTerm, EvaluationCriterion, ProjectType
from .project import Project
from .project_member import ProjectMember
from .user import User, UserRole

__all__ = [
    "Course",
    "CourseLink",
    "CourseTerm",
    "EvaluationCriterion",
    "Project",
    "ProjectMember",
    "ProjectType",
    "User",
    "UserRole",
]
