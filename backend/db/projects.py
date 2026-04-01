from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlmodel import Session

from models.course import Course, CourseTerm
from models.course_lecturer import CourseLecturer
from models.project import Project
from models.project_member import ProjectMember
from models.user import User


def _escape_like(value: str) -> str:
    """Escape LIKE special characters in ``value`` so they are matched literally.

    Without escaping, a user-supplied ``%`` or ``_`` would be treated as a wildcard,
    potentially returning more results than intended.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_projects(
    session: Session,
    *,
    q: str | None = None,
    course: str | None = None,
    year: int | None = None,
    term: CourseTerm | None = None,
    lecturer: str | None = None,
    technology: str | None = None,
) -> list[tuple[Project, Course]]:
    """Query projects and their associated courses, applying optional filters.

    Joins ``project`` with ``course`` and applies each supplied filter. The lecturer filter
    performs a further join with ``course_lecturer`` and ``user`` so that only projects taught
    by a matching lecturer are returned.
    """
    stmt = select(Project, Course).join(Course, Project.course_id == Course.id)

    if q:
        escaped = _escape_like(q)
        stmt = stmt.where(
            or_(
                Project.title.ilike(f"%{escaped}%", escape="\\"),
                Project.description.ilike(f"%{escaped}%", escape="\\"),
            )
        )

    if course:
        stmt = stmt.where(Course.code == course)

    if year is not None:
        stmt = stmt.where(Project.academic_year == year)

    if term is not None:
        stmt = stmt.where(Course.term == term)

    if lecturer:
        escaped_lecturer = _escape_like(lecturer)
        stmt = (
            stmt.join(CourseLecturer, Course.id == CourseLecturer.course_id)
            .join(User, CourseLecturer.user_id == User.id)
            .where(
                or_(
                    User.name.ilike(f"%{escaped_lecturer}%", escape="\\"),
                    User.email.ilike(f"%{escaped_lecturer}%", escape="\\"),
                )
            )
        )

    if technology:
        # Filter projects whose JSONB technologies array contains the given string.
        # ``@>`` is PostgreSQL's "contains" operator for JSONB.
        stmt = stmt.where(Project.technologies.op("@>")(func.jsonb_build_array(technology)))

    rows = session.execute(stmt).all()
    return [(row[0], row[1]) for row in rows]


def get_project_members(
    session: Session,
    project_ids: list[int],
) -> dict[int, list[User]]:
    """Return a mapping from project id to its list of member users.

    Only projects whose ids appear in ``project_ids`` are queried.
    """
    if not project_ids:
        return {}

    stmt = (
        select(ProjectMember.project_id, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id.in_(project_ids))
    )

    result: dict[int, list[User]] = {}
    for project_id, user in session.execute(stmt).all():
        result.setdefault(project_id, []).append(user)
    return result


def get_course_lecturers(
    session: Session,
    course_ids: list[int],
) -> dict[int, list[User]]:
    """Return a mapping from course id to its list of lecturer users.

    Only courses whose ids appear in ``course_ids`` are queried.
    """
    if not course_ids:
        return {}

    stmt = (
        select(CourseLecturer.course_id, User)
        .join(User, CourseLecturer.user_id == User.id)
        .where(CourseLecturer.course_id.in_(course_ids))
    )

    result: dict[int, list[User]] = {}
    for course_id, user in session.execute(stmt).all():
        result.setdefault(course_id, []).append(user)
    return result
