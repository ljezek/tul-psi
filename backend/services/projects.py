from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.projects import (
    get_course_lecturers,
    get_project_members,
    get_projects,
)
from db.projects import (
    get_project as db_get_project,
)
from models.course import Course, CourseTerm
from models.project import Project
from models.user import User
from schemas.projects import CoursePublic, LecturerPublic, MemberPublic, ProjectPublic


def _require_id(user: User) -> int:
    """Return ``user.id``, raising ``ValueError`` if it is ``None``.

    ``User.id`` is typed as ``int | None`` because SQLModel allows unsaved instances,
    but any row returned from the database always has a non-None primary key.
    This helper surfaces the inconsistency early with a clear message rather than
    letting it propagate as a silent ``None``.
    """
    if user.id is None:
        raise ValueError(f"User returned from DB has no id: {user!r}")
    return user.id


def _build_project_public(
    p: Project,
    c: Course,
    members: list[User],
    lecturers: list[User],
) -> ProjectPublic:
    """Assemble a ``ProjectPublic`` from a project row, its course, members, and lecturers.

    Raises ``ValueError`` if the project or course row has a ``None`` primary key, which
    should never happen for rows fetched from the database.
    """
    if p.id is None:
        raise ValueError(f"Project returned from DB has no id: {p!r}")
    if c.id is None:
        raise ValueError(f"Course returned from DB has no id: {c!r}")
    return ProjectPublic(
        id=p.id,
        title=p.title,
        description=p.description,
        github_url=p.github_url,
        live_url=p.live_url,
        technologies=p.technologies,
        academic_year=p.academic_year,
        course=CoursePublic(
            code=c.code,
            name=c.name,
            syllabus=c.syllabus,
            term=c.term,
            project_type=c.project_type,
            min_score=c.min_score,
            peer_bonus_budget=c.peer_bonus_budget,
            evaluation_criteria=c.evaluation_criteria,
            links=c.links,
            lecturers=[LecturerPublic(name=u.name, github_alias=u.github_alias) for u in lecturers],
        ),
        members=[
            MemberPublic(
                id=_require_id(m),
                github_alias=m.github_alias,
                name=m.name,
            )
            for m in members
        ],
    )


class ProjectsService:
    """Business logic for the projects discovery endpoint.

    This service assembles the full ``ProjectPublic`` response by combining the main
    project+course query with separate member and lecturer lookups, keeping each DB
    round-trip clearly separated.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_projects(
        self,
        *,
        q: str | None = None,
        course: str | None = None,
        year: int | None = None,
        term: CourseTerm | None = None,
        lecturer: str | None = None,
        technology: str | None = None,
    ) -> list[ProjectPublic]:
        """Return all projects matching the supplied filter criteria.

        Each returned ``ProjectPublic`` includes a nested course summary (with lecturers)
        and the full list of current project members.
        """
        rows = await get_projects(
            self._session,
            q=q,
            course=course,
            year=year,
            term=term,
            lecturer=lecturer,
            technology=technology,
        )

        # Persisted rows always have a non-None id; collect ids to drive bulk lookups.
        project_ids = [p.id for p, _ in rows if p.id is not None]
        course_ids = list({c.id for _, c in rows if c.id is not None})
        members_by_project = await get_project_members(self._session, project_ids)
        lecturers_by_course = await get_course_lecturers(self._session, course_ids)

        return [
            _build_project_public(
                p,
                c,
                members_by_project.get(p.id, []) if p.id is not None else [],
                lecturers_by_course.get(c.id, []) if c.id is not None else [],
            )
            for p, c in rows
        ]

    async def get_project(self, project_id: int) -> ProjectPublic | None:
        """Return the project with the given ``project_id``, or ``None`` if not found.

        Assembles the full ``ProjectPublic`` response including the nested course
        summary (with lecturers) and the project's member list.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            return None

        p, c = row
        project_id_list = [p.id] if p.id is not None else []
        course_id_list = [c.id] if c.id is not None else []
        members_by_project = await get_project_members(self._session, project_id_list)
        lecturers_by_course = await get_course_lecturers(self._session, course_id_list)
        return _build_project_public(
            p,
            c,
            members_by_project.get(p.id, []) if p.id is not None else [],
            lecturers_by_course.get(c.id, []) if c.id is not None else [],
        )
