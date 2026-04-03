from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.users import get_or_create_user as get_or_create_user
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

    Results are ordered by ``updated_at`` ascending so that the earliest
    submission appears first — useful for deterministic display order.
    """
    stmt = (
        select(ProjectEvaluation)
        .where(ProjectEvaluation.project_id == project_id)
        .order_by(ProjectEvaluation.updated_at)
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

    Results are ordered by ``updated_at`` ascending.
    """
    stmt = (
        select(CourseEvaluation)
        .join(Project, CourseEvaluation.project_id == Project.id)
        .where(Project.course_id == course_id)
        .order_by(CourseEvaluation.updated_at)
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


async def is_project_member(
    session: AsyncSession,
    project_id: int,
    user_id: int,
) -> bool:
    """Return ``True`` when *user_id* is a member of *project_id*.

    Used to gate write operations so that only current project members (and
    lecturers — checked separately) may update the project or add new members.
    """
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )
    row = (await session.execute(stmt)).first()
    return row is not None


async def is_course_lecturer(
    session: AsyncSession,
    project_id: int,
    user_id: int,
) -> bool:
    """Return ``True`` when *user_id* is a lecturer on the course that owns *project_id*.

    Joins through ``project`` → ``course_lecturer`` to resolve the relationship.
    """
    stmt = (
        select(CourseLecturer)
        .join(Project, CourseLecturer.course_id == Project.course_id)
        .where(
            Project.id == project_id,
            CourseLecturer.user_id == user_id,
        )
    )
    row = (await session.execute(stmt)).first()
    return row is not None


async def update_project(
    session: AsyncSession,
    project_id: int,
    *,
    title: str | None = None,
    description: str | None = None,
    github_url: str | None = None,
    live_url: str | None = None,
    technologies: list[str] | None = None,
) -> Project | None:
    """Apply the supplied field changes to the project identified by *project_id*.

    Only fields whose keyword arguments are not ``None`` are written.  Returns the
    updated ``Project`` row, or ``None`` when no project with *project_id* exists.
    The caller must commit the session after a successful return.
    """
    stmt = select(Project).where(Project.id == project_id)
    project = (await session.execute(stmt)).scalars().first()
    if project is None:
        return None

    if title is not None:
        project.title = title
    if description is not None:
        project.description = description
    if github_url is not None:
        project.github_url = github_url
    if live_url is not None:
        project.live_url = live_url
    if technologies is not None:
        project.technologies = technologies

    session.add(project)
    return project


async def add_project_member(
    session: AsyncSession,
    project_id: int,
    user_id: int,
    invited_by: int,
) -> tuple[ProjectMember, bool]:
    """Add *user_id* as a member of *project_id*, invited by *invited_by*.

    Uses an UPSERT (INSERT … ON CONFLICT DO NOTHING) against the unique constraint
    ``uq_project_member_project_user`` so concurrent invites for the same user
    are handled atomically without a race-prone SELECT before INSERT.

    Returns a ``(member, created)`` tuple.  When the user is already a member
    ``created`` is ``False`` and the existing row is returned unchanged.
    The caller must commit the session after a successful return.
    """
    stmt = (
        pg_insert(ProjectMember)
        .values(
            project_id=project_id,
            user_id=user_id,
            invited_by=invited_by,
            invited_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(constraint="uq_project_member_project_user")
    )
    result = await session.execute(stmt)
    created = result.rowcount > 0
    # Fetch the full ORM object whether just inserted or pre-existing.
    member = (
        (
            await session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if member is None:
        raise RuntimeError(
            f"Expected member row for user {user_id} in project {project_id} after UPSERT."
        )
    return member, created


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

    # Use a subselect to atomically find and delete peer_feedback rows that belong
    # to this project's course evaluations.
    await session.execute(
        delete(PeerFeedback).where(
            PeerFeedback.course_evaluation_id.in_(
                select(CourseEvaluation.id).where(CourseEvaluation.project_id == project_id)
            )
        )
    )
    await session.execute(delete(CourseEvaluation).where(CourseEvaluation.project_id == project_id))
    await session.execute(
        delete(ProjectEvaluation).where(ProjectEvaluation.project_id == project_id)
    )
    await session.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
    await session.execute(delete(Project).where(Project.id == project_id))
    await session.flush()
    return True


async def get_project_evaluation_by_lecturer(
    session: AsyncSession,
    project_id: int,
    lecturer_id: int,
) -> ProjectEvaluation | None:
    """Return the evaluation submitted by *lecturer_id* for *project_id*, or ``None``.

    Used by the GET endpoint so that a lecturer can retrieve only their own row
    before results are unlocked.
    """
    stmt = select(ProjectEvaluation).where(
        ProjectEvaluation.project_id == project_id,
        ProjectEvaluation.lecturer_id == lecturer_id,
    )
    return (await session.execute(stmt)).scalars().first()


async def upsert_project_evaluation(
    session: AsyncSession,
    project_id: int,
    lecturer_id: int,
    scores: list[dict[str, object]],
    *,
    submitted: bool,
) -> ProjectEvaluation:
    """Insert or update the evaluation row for *(project_id, lecturer_id)*.

    Uses an UPSERT so that the lecturer can save a draft (``submitted=False``)
    and later update or finalise it (``submitted=True``) without conflicts.
    The caller is responsible for committing the session after this call.
    """
    stmt = (
        pg_insert(ProjectEvaluation)
        .values(
            project_id=project_id,
            lecturer_id=lecturer_id,
            scores=scores,
            submitted=submitted,
            updated_at=datetime.now(UTC),
        )
        .on_conflict_do_update(
            index_elements=["project_id", "lecturer_id"],
            set_={
                "scores": scores,
                "submitted": submitted,
                "updated_at": datetime.now(UTC),
            },
        )
    )
    await session.execute(stmt)
    await session.flush()
    # Fetch the full ORM object after upsert to return consistent data.
    evaluation = (
        (
            await session.execute(
                select(ProjectEvaluation).where(
                    ProjectEvaluation.project_id == project_id,
                    ProjectEvaluation.lecturer_id == lecturer_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if evaluation is None:
        raise RuntimeError(
            f"Expected project_evaluation row for lecturer {lecturer_id}"
            f" in project {project_id} after UPSERT."
        )
    return evaluation


async def get_lecturer_evaluation_statuses(
    session: AsyncSession,
    project_id: int,
    course_id: int,
) -> list[tuple[User, bool]]:
    """Return all lecturers assigned to *course_id* with their project-evaluation status.

    Each entry is ``(user, submitted)`` where ``submitted`` is ``True`` when the
    lecturer has a ``ProjectEvaluation`` row for *project_id* with ``submitted=True``,
    and ``False`` otherwise (no row or draft).  Uses a LEFT JOIN so that lecturers
    who have not yet saved any evaluation are still included.
    """
    submitted_flag = func.coalesce(ProjectEvaluation.submitted, False).label("submitted")
    stmt = (
        select(User, submitted_flag)
        .select_from(CourseLecturer)
        .join(User, User.id == CourseLecturer.user_id)
        .outerjoin(
            ProjectEvaluation,
            and_(
                ProjectEvaluation.project_id == project_id,
                ProjectEvaluation.lecturer_id == CourseLecturer.user_id,
            ),
        )
        .where(CourseLecturer.course_id == course_id)
    )
    rows = (await session.execute(stmt)).all()
    return [(user, bool(submitted)) for user, submitted in rows]


async def get_member_evaluation_statuses(
    session: AsyncSession,
    project_id: int,
) -> list[tuple[User, bool]]:
    """Return all members of *project_id* with their course-evaluation status.

    Each entry is ``(user, submitted)`` where ``submitted`` is ``True`` when the
    member has a ``CourseEvaluation`` row for *project_id* with ``submitted=True``,
    and ``False`` otherwise.  Uses a LEFT JOIN so that members who have not yet
    saved any evaluation are still included.
    """
    submitted_flag = func.coalesce(CourseEvaluation.submitted, False).label("submitted")
    stmt = (
        select(User, submitted_flag)
        .select_from(ProjectMember)
        .join(User, User.id == ProjectMember.user_id)
        .outerjoin(
            CourseEvaluation,
            and_(
                CourseEvaluation.project_id == project_id,
                CourseEvaluation.student_id == ProjectMember.user_id,
            ),
        )
        .where(ProjectMember.project_id == project_id)
    )
    rows = (await session.execute(stmt)).all()
    return [(user, bool(submitted)) for user, submitted in rows]


async def get_course_evaluation_by_student(
    session: AsyncSession,
    project_id: int,
    student_id: int,
) -> CourseEvaluation | None:
    """Return the course evaluation row for *student_id* on *project_id*, or ``None``.

    Used by the GET endpoint so that a student can retrieve their own draft or
    submitted row before results are unlocked.
    """
    stmt = select(CourseEvaluation).where(
        CourseEvaluation.project_id == project_id,
        CourseEvaluation.student_id == student_id,
    )
    return (await session.execute(stmt)).scalars().first()


async def upsert_course_evaluation(
    session: AsyncSession,
    project_id: int,
    student_id: int,
    *,
    rating: int | None,
    strengths: str | None,
    improvements: str | None,
    submitted: bool,
) -> CourseEvaluation:
    """Insert or update the course evaluation row for *(project_id, student_id)*.

    Uses an UPSERT so that the student can save a draft (``submitted=False``)
    and later update or finalise it (``submitted=True``) without conflicts.
    The caller is responsible for committing the session after this call.
    """
    stmt = (
        pg_insert(CourseEvaluation)
        .values(
            project_id=project_id,
            student_id=student_id,
            rating=rating,
            strengths=strengths,
            improvements=improvements,
            submitted=submitted,
            updated_at=datetime.now(UTC),
        )
        .on_conflict_do_update(
            constraint="uq_course_evaluation_project_student",
            set_={
                "rating": rating,
                "strengths": strengths,
                "improvements": improvements,
                "submitted": submitted,
                "updated_at": datetime.now(UTC),
            },
        )
    )
    await session.execute(stmt)
    await session.flush()
    # Fetch the full ORM object after upsert to return consistent data.
    evaluation = (
        (
            await session.execute(
                select(CourseEvaluation).where(
                    CourseEvaluation.project_id == project_id,
                    CourseEvaluation.student_id == student_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if evaluation is None:
        raise RuntimeError(
            f"Expected course_evaluation row for student {student_id}"
            f" in project {project_id} after UPSERT."
        )
    return evaluation


async def replace_peer_feedback(
    session: AsyncSession,
    course_evaluation_id: int,
    items: list[dict[str, object]],
) -> None:
    """Replace all peer feedback rows for *course_evaluation_id* with *items*.

    Deletes all existing ``PeerFeedback`` rows for the evaluation, adds the
    provided items to the session, and flushes the pending changes.  Passing
    an empty list clears all existing feedback.  The caller is responsible for
    committing the session.
    """
    await session.execute(
        delete(PeerFeedback).where(PeerFeedback.course_evaluation_id == course_evaluation_id)
    )
    for item in items:
        feedback = PeerFeedback(
            course_evaluation_id=course_evaluation_id,
            receiving_student_id=int(item["receiving_student_id"]),  # type: ignore[arg-type]
            strengths=item.get("strengths"),  # type: ignore[arg-type]
            improvements=item.get("improvements"),  # type: ignore[arg-type]
            bonus_points=int(item.get("bonus_points", 0)),  # type: ignore[arg-type]
        )
        session.add(feedback)
    await session.flush()


async def get_projects_for_course(
    session: AsyncSession,
    course_id: int,
    *,
    year: int | None = None,
) -> list[Project]:
    """Return all projects for *course_id*, ordered by year descending then title ascending.

    When *year* is provided the results are further filtered to that academic year.
    """
    stmt = (
        select(Project)
        .where(Project.course_id == course_id)
        .order_by(Project.academic_year.desc(), Project.title)
    )
    if year is not None:
        stmt = stmt.where(Project.academic_year == year)
    return list((await session.execute(stmt)).scalars().all())


async def get_submitted_project_evaluations(
    session: AsyncSession,
    project_ids: list[int],
) -> dict[int, list[ProjectEvaluation]]:
    """Return submitted lecturer evaluations grouped by project id.

    Only rows with ``submitted=True`` are included so that draft evaluations
    are excluded from the aggregation used by the overview endpoint.
    """
    if not project_ids:
        return {}

    stmt = select(ProjectEvaluation).where(
        ProjectEvaluation.project_id.in_(project_ids),
        ProjectEvaluation.submitted.is_(True),
    )
    result: dict[int, list[ProjectEvaluation]] = {}
    for ev in (await session.execute(stmt)).scalars().all():
        result.setdefault(ev.project_id, []).append(ev)
    return result


async def get_submitted_course_evaluations_for_projects(
    session: AsyncSession,
    project_ids: list[int],
) -> dict[int, list[CourseEvaluation]]:
    """Return submitted student course evaluations grouped by project id.

    Only rows with ``submitted=True`` are included so that draft evaluations
    are excluded from the aggregation used by the overview endpoint.
    """
    if not project_ids:
        return {}

    stmt = select(CourseEvaluation).where(
        CourseEvaluation.project_id.in_(project_ids),
        CourseEvaluation.submitted.is_(True),
    )
    result: dict[int, list[CourseEvaluation]] = {}
    for ev in (await session.execute(stmt)).scalars().all():
        result.setdefault(ev.project_id, []).append(ev)
    return result


async def get_peer_feedback_with_users_for_projects(
    session: AsyncSession,
    project_ids: list[int],
) -> dict[int, list[tuple[PeerFeedback, User]]]:
    """Return submitted peer feedback rows for *project_ids*, grouped by project id.

    Each entry is ``(peer_feedback, receiving_user)`` so that callers can
    display the receiving student's name without a further lookup. Uses an
    explicit join chain through ``course_evaluation`` to resolve the project
    association and excludes draft course evaluations from the overview data.
    """
    if not project_ids:
        return {}

    stmt = (
        select(CourseEvaluation.project_id, PeerFeedback, User)
        .select_from(PeerFeedback)
        .join(CourseEvaluation, PeerFeedback.course_evaluation_id == CourseEvaluation.id)
        .join(User, PeerFeedback.receiving_student_id == User.id)
        .where(
            CourseEvaluation.project_id.in_(project_ids),
            CourseEvaluation.submitted.is_(True),
        )
    )
    result: dict[int, list[tuple[PeerFeedback, User]]] = {}
    for project_id, feedback, user in (await session.execute(stmt)).all():
        result.setdefault(project_id, []).append((feedback, user))
    return result


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
