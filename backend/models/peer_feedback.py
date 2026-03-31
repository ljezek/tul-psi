from __future__ import annotations

from typing import ClassVar

from sqlmodel import Field, SQLModel


class PeerFeedback(SQLModel, table=True):
    """Peer feedback submitted as part of a student's course evaluation.

    Each row represents one student's feedback about a single teammate.
    Multiple ``PeerFeedback`` rows can belong to the same ``CourseEvaluation``
    — one per teammate in a TEAM project.  ``bonus_points`` distributes the
    caller's share of ``Course.peer_bonus_budget``; it is zero when peer
    bonuses are disabled for the course.
    """

    __tablename__: ClassVar[str] = "peer_feedback"

    id: int | None = Field(default=None, primary_key=True)
    course_evaluation_id: int = Field(foreign_key="course_evaluation.id")
    receiving_student_id: int = Field(foreign_key="user.id")
    # Null means the student has not yet written the free-text sections (draft).
    strengths: str | None = Field(default=None)
    improvements: str | None = Field(default=None)
    # Zero when peer bonuses are not enabled for this course.
    bonus_points: int = Field(default=0)
