from __future__ import annotations

from .course import Course, CourseLink, CourseTerm, EvaluationCriterion, ProjectType
from .course_evaluation import CourseEvaluation
from .course_lecturer import CourseLecturer
from .otp_token import OtpToken
from .peer_feedback import PeerFeedback
from .project import Project
from .project_evaluation import EvaluationScore, ProjectEvaluation
from .project_member import ProjectMember
from .user import User, UserRole

__all__ = [
    "Course",
    "CourseEvaluation",
    "CourseLecturer",
    "CourseLink",
    "CourseTerm",
    "EvaluationCriterion",
    "EvaluationScore",
    "OtpToken",
    "PeerFeedback",
    "Project",
    "ProjectEvaluation",
    "ProjectMember",
    "ProjectType",
    "User",
    "UserRole",
]
