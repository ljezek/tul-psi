from __future__ import annotations

from pydantic import BaseModel


class Project(BaseModel):
    id: int
    title: str
    academic_year: str
    subject: str
    technologies: list[str]
    students: list[str] = []
