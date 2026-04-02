from __future__ import annotations

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course, CourseTerm
from models.course_evaluation import CourseEvaluation
from models.course_lecturer import CourseLecturer
from models.peer_feedback import PeerFeedback
from models.project import Project
from models.project_evaluation import ProjectEvaluation
from models.project_member import ProjectMember
from models.user import User


def _escape_like(value: str) -> str:
    """Escape LIKE special characters in ``value`` so they are matched literally.

    Without escaping, a user-supplied ``%`` or ``_`` would be treated as a wildcard,
    potentially returning more results than intended.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def get_projects(
    session: AsyncSession,
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
        # Use an EXISTS subquery instead of a join to avoid duplicate (Project, Course) rows
        # when a course has multiple lecturers that all match the search term.
        lecturer_subq = (
            select(1)
            .select_from(CourseLecturer)
            .join(User, CourseLecturer.user_id == User.id)
            .where(
                CourseLecturer.course_id == Course.id,
                or_(
                    User.name.ilike(f"%{escaped_lecturer}%", escape="\\"),
                    User.email.ilike(f"%{escaped_lecturer}%", escape="\\"),
                ),
            )
        )
        stmt = stmt.where(lecturer_subq.exists())

    if technology:
        # Filter projects whose JSONB technologies array contains the given string.
        # ``@>`` is PostgreSQL's "contains" operator for JSONB.
        stmt = stmt.where(Project.technologies.op("@>")(func.jsonb_build_array(technology)))

    rows = (await session.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def get_project(
    session: AsyncSession,
    project_id: int,
) -> tuple[Project, Course] | None:
    """Return the project with the given ``project_id`` and its associated course.

    Returns ``None`` when no project with the given id exists.
    """
    stmt = (
        select(Project, Course)
        .join(Course, Project.course_id == Course.id)
        .where(Project.id == project_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return (row[0], row[1])


async def get_project_members(
    session: AsyncSession,
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
    for project_id, user in (await session.execute(stmt)).all():
        result.setdefault(project_id, []).append(user)
    return result


async def get_course_lecturers(
    session: AsyncSession,
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
    for course_id, user in (await session.execute(stmt)).all():
        result.setdefault(course_id, []).append(user)
    return result


async def get_project_evaluations(
    session: AsyncSession,
    project_id: int,
) -> list[ProjectEvaluation]:
    """Return all lecturer evaluations submitted for *project_id*.

    Results are ordered by ``submitted_at`` ascending so that the earliest
    submission appears first — useful for deterministic display order.
    """
    stmt = (
        select(ProjectEvaluation)
        .where(ProjectEvaluation.project_id == project_id)
        .order_by(ProjectEvaluation.submitted_at)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_course_evaluations(
    session: AsyncSession,
    course_id: int,
    *,
    academic_year: int | None = None,
) -> list[CourseEvaluation]:
    """Return all student course evaluations for the course identified by *course_id*.

    Joins through the ``project`` table to resolve the course association.
    Optionally narrows results to a specific *academic_year* when provided, which
    is useful for showing only the current cohort's evaluations on a course page.

    Results are ordered by ``submitted_at`` ascending.
    """
    stmt = (
        select(CourseEvaluation)
        .join(Project, CourseEvaluation.project_id == Project.id)
        .where(Project.course_id == course_id)
        .order_by(CourseEvaluation.submitted_at)
    )
    if academic_year is not None:
        stmt = stmt.where(Project.academic_year == academic_year)
    return list((await session.execute(stmt)).scalars().all())


async def get_peer_feedback_received(
    session: AsyncSession,
    project_id: int,
    receiving_student_id: int,
) -> list[PeerFeedback]:
    """Return peer feedback rows *addressed to* ``receiving_student_id`` for ``project_id``.

    Joins through ``course_evaluation`` to scope the lookup to a single project.
    """
    stmt = (
        select(PeerFeedback)
        .join(CourseEvaluation, PeerFeedback.course_evaluation_id == CourseEvaluation.id)
        .where(
            CourseEvaluation.project_id == project_id,
            PeerFeedback.receiving_student_id == receiving_student_id,
        )
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_peer_feedback_authored(
    session: AsyncSession,
    project_id: int,
    author_student_id: int,
) -> list[PeerFeedback]:
    """Return peer feedback rows *written by* ``author_student_id`` for ``project_id``.

    Joins through ``course_evaluation`` so that only feedback originating from
    the author's own course evaluation for this project is returned.
    """
    stmt = (
        select(PeerFeedback)
        .join(CourseEvaluation, PeerFeedback.course_evaluation_id == CourseEvaluation.id)
        .where(
            CourseEvaluation.project_id == project_id,
            CourseEvaluation.student_id == author_student_id,
        )
    )
    return list((await session.execute(stmt)).scalars().all())


async def create_project(
    session: AsyncSession,
    *,
    course_id: int,
    title: str,
    description: str | None,
    github_url: str | None,
    live_url: str | None,
    technologies: list[str],
    academic_year: int,
) -> Project:
    """Insert a new ``Project`` row and return it with the generated primary key.

    The caller is responsible for committing the session after this call.
    ``session.flush()`` is used to obtain the generated primary key without
    a full commit, allowing the caller to stage further related changes (e.g.
    ``ProjectMember``) in the same transaction.
    """
    project = Project(
        title=title,
        description=description,
        github_url=github_url,
        live_url=live_url,
        technologies=technologies,
        academic_year=academic_year,
        course_id=course_id,
    )
    session.add(project)
    await session.flush()
    return project


async def add_project_member(
    session: AsyncSession,
    *,
    project_id: int,
    user_id: int,
    invited_by: int | None = None,
) -> ProjectMember:
    """Insert a ``ProjectMember`` row linking *user_id* to *project_id*.

    ``invited_by`` is the id of the lecturer who performed the seeding action;
    pass ``None`` when the member is added without an explicit inviter.
    The caller is responsible for committing the session after this call.
    """
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        invited_by=invited_by,
    )
    session.add(member)
    await session.flush()
    return member


async def delete_project(session: AsyncSession, project_id: int) -> bool:
    """Delete the project with *project_id* and all its dependent rows.

    Rows are removed in dependency order to satisfy foreign-key constraints:
    1. ``peer_feedback`` rows linked via ``course_evaluation``
    2. ``course_evaluation`` rows for the project
    3. ``project_evaluation`` rows for the project
    4. ``project_member`` rows for the project
    5. The ``project`` row itself

    Returns ``True`` when a row was found and deleted, ``False`` when no such
    project exists.  The caller is responsible for committing the session.
    """
    project = (
        (await session.execute(select(Project).where(Project.id == project_id))).scalars().first()
    )
    if project is None:
        return False

    # Collect course_evaluation ids so we can delete their peer_feedback rows.
    eval_ids_stmt = select(CourseEvaluation.id).where(CourseEvaluation.project_id == project_id)
    eval_ids = list((await session.execute(eval_ids_stmt)).scalars().all())

    if eval_ids:
        await session.execute(
            delete(PeerFeedback).where(PeerFeedback.course_evaluation_id.in_(eval_ids))
        )
    await session.execute(delete(CourseEvaluation).where(CourseEvaluation.project_id == project_id))
    await session.execute(
        delete(ProjectEvaluation).where(ProjectEvaluation.project_id == project_id)
    )
    await session.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
    await session.execute(delete(Project).where(Project.id == project_id))
    await session.flush()
    return True


async def unlock_project_results(session: AsyncSession, project_id: int) -> Project | None:
    """Set ``results_unlocked=True`` on the project identified by *project_id*.

    Returns the updated ``Project`` row, or ``None`` when no such project exists.
    The caller is responsible for committing the session after this call.
    """
    project = (
        (await session.execute(select(Project).where(Project.id == project_id))).scalars().first()
    )
    if project is None:
        return None
    project.results_unlocked = True
    session.add(project)
    await session.flush()
    return project
