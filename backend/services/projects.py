from __future__ import annotations

from sqlmodel import Session

from db.projects import get_project_members, get_projects
from models.course import CourseTerm
from schemas.projects import CoursePublic, MemberPublic, ProjectPublic


class ProjectsService:
    """Business logic for the projects discovery endpoint.

    This service assembles the full ``ProjectPublic`` response by combining
    the main project+course query with a separate members lookup, keeping
    the two DB round-trips clearly separated.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_projects(
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

        Each returned ``ProjectPublic`` includes a nested course summary and
        the full list of current project members.
        """
        rows = get_projects(
            self._session,
            q=q,
            course=course,
            year=year,
            term=term,
            lecturer=lecturer,
            technology=technology,
        )

        # Persisted rows always have a non-None id; assert to surface any
        # unexpected inconsistency early rather than propagating None silently.
        project_ids = [p.id for p, _ in rows if p.id is not None]
        members_by_project = get_project_members(self._session, project_ids)

        result: list[ProjectPublic] = []
        for p, c in rows:
            # Persisted rows always have a non-None id; raise early to surface any
            # unexpected inconsistency rather than propagating None silently.
            if p.id is None:
                raise ValueError(f"Project returned from DB has no id: {p!r}")
            if c.id is None:
                raise ValueError(f"Course returned from DB has no id: {c!r}")
            result.append(
                ProjectPublic(
                    id=p.id,
                    title=p.title,
                    description=p.description,
                    github_url=p.github_url,
                    live_url=p.live_url,
                    technologies=p.technologies,
                    academic_year=p.academic_year,
                    course=CoursePublic(
                        id=c.id,
                        code=c.code,
                        name=c.name,
                        term=c.term,
                    ),
                    members=[
                        MemberPublic(
                            id=m.id,  # type: ignore[arg-type]  # m.id is always set for DB rows
                            github_alias=m.github_alias,
                            name=m.name,
                        )
                        for m in members_by_project.get(p.id, [])
                    ],
                )
            )
        return result
