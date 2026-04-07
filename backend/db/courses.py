from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.course_evaluation import CourseEvaluation
from models.course_lecturer import CourseLecturer
from models.project import Project
from models.project_evaluation import ProjectEvaluation
from models.user import User
from schemas.courses import CourseCreate, CourseUpdate


async def get_courses(session: AsyncSession) -> list[Course]:
    """Return all courses ordered by course code."""
    stmt = select(Course).order_by(Course.code)
    return list((await session.execute(stmt)).scalars().all())


async def get_course(session: AsyncSession, course_id: int) -> Course | None:
    """Return the course with the given ``course_id``, or ``None`` if not found."""
    stmt = select(Course).where(Course.id == course_id)
    return (await session.execute(stmt)).scalars().first()


async def get_course_by_code(session: AsyncSession, code: str) -> Course | None:
    """Return the course with the given ``code``, or ``None`` if not found."""
    stmt = select(Course).where(Course.code == code)
    return (await session.execute(stmt)).scalars().first()


async def create_course(
    session: AsyncSession,
    data: CourseCreate,
    created_by: int,
) -> Course:
    """Insert a new course row and return it with the DB-generated primary key.

    The caller is responsible for committing the session after this call so
    that the insert and any related operations form a single unit of work.
    ``session.flush()`` is used to materialise the auto-assigned ``id``
    without ending the transaction.
    """
    course = Course(**data.model_dump(), created_by=created_by)
    session.add(course)
    await session.flush()
    return course


async def update_course(
    session: AsyncSession,
    course: Course,
    data: CourseUpdate,
) -> Course:
    """Apply ``data`` fields to ``course`` and stage the update.

    Only fields explicitly provided in the request body are written
    (``model_dump(exclude_unset=True)``).  The caller is responsible for
    committing the session.  ``session.flush()`` is called to propagate the
    changes within the current transaction so that a subsequent SELECT sees
    the updated values.
    """
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(course, field, value)
    session.add(course)
    await session.flush()
    return course


async def get_course_project_stats(
    session: AsyncSession,
    course_ids: list[int],
) -> dict[int, tuple[int, list[int]]]:
    """Return a mapping from course id to ``(project_count, sorted_academic_years)``.

    Courses with no projects will not appear in the mapping; callers should
    handle missing keys by using a default of ``(0, [])``.
    """
    if not course_ids:
        return {}

    stmt = (
        select(
            Project.course_id,
            func.count(Project.id).label("project_count"),
            func.array_agg(func.distinct(Project.academic_year)).label("academic_years"),
        )
        .where(Project.course_id.in_(course_ids))
        .group_by(Project.course_id)
    )

    result: dict[int, tuple[int, list[int]]] = {}
    for row in (await session.execute(stmt)).all():
        years: list[int] = sorted(row.academic_years) if row.academic_years else []
        result[row.course_id] = (row.project_count, years)
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
        .order_by(User.name)
    )

    result: dict[int, list[User]] = {}
    for course_id, user in (await session.execute(stmt)).all():
        result.setdefault(course_id, []).append(user)
    return result


async def get_course_evaluations(
    session: AsyncSession,
    course_id: int,
) -> list[CourseEvaluation]:
    """Return all course evaluations for projects with ``results_unlocked`` in the given course.

    Only projects whose ``results_unlocked`` flag is ``True`` are considered,
    ensuring that the data is aligned with the student-facing results visibility.
    Both draft and submitted evaluations are returned so that admin and lecturer
    users have full visibility.
    """
    stmt = (
        select(CourseEvaluation)
        .join(Project, CourseEvaluation.project_id == Project.id)
        .where(
            Project.course_id == course_id,
            Project.results_unlocked.is_(True),
        )
        .order_by(CourseEvaluation.project_id, CourseEvaluation.id)
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_course_lecturer(
    session: AsyncSession,
    course_id: int,
    user_id: int,
) -> bool:
    """Assign *user_id* as a lecturer on *course_id*.

    Uses an UPSERT (INSERT … ON CONFLICT DO NOTHING) against the composite
    primary key ``(course_id, user_id)`` so concurrent assignments for the
    same pair are handled atomically.

    Returns ``True`` when the row was inserted and ``False`` when the lecturer
    was already assigned.  The caller must commit the session after a
    successful return.
    """
    stmt = (
        pg_insert(CourseLecturer)
        .values(
            course_id=course_id,
            user_id=user_id,
            assigned_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(index_elements=["course_id", "user_id"])
    )
    result = await session.execute(stmt)
    return result.rowcount > 0


async def remove_course_lecturer(
    session: AsyncSession,
    course_id: int,
    user_id: int,
) -> bool:
    """Remove the lecturer assignment for *user_id* from *course_id*.

    Returns ``True`` when a row was deleted, ``False`` when no assignment
    existed.  The caller must commit the session after a successful return.
    """
    stmt = delete(CourseLecturer).where(
        CourseLecturer.course_id == course_id,
        CourseLecturer.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.rowcount > 0


async def get_pending_lecturer_evaluations_count(
    session: AsyncSession,
    course_ids: list[int],
    user_id: int,
) -> dict[int, int]:
    """Return a mapping from course id to the number of projects needing evaluation by *user_id*.

    A project needs evaluation if the lecturer is assigned to the course,
    the project results are NOT unlocked, and the lecturer hasn't submitted
    a final evaluation for that project yet.
    """
    if not course_ids:
        return {}

    # Find projects in these courses where results are not unlocked.
    stmt = select(Project.id, Project.course_id).where(
        Project.course_id.in_(course_ids),
        Project.results_unlocked.is_(False),
    )
    projects = (await session.execute(stmt)).all()
    if not projects:
        return {cid: 0 for cid in course_ids}

    project_ids = [p.id for p in projects]

    # Find projects that have a submitted evaluation from this user.
    submitted_stmt = select(ProjectEvaluation.project_id).where(
        ProjectEvaluation.project_id.in_(project_ids),
        ProjectEvaluation.lecturer_id == user_id,
        ProjectEvaluation.submitted.is_(True),
    )
    submitted_ids = set((await session.execute(submitted_stmt)).scalars().all())

    # Count projects per course that are not in submitted_ids.
    result: dict[int, int] = {cid: 0 for cid in course_ids}
    for p_id, c_id in projects:
        if p_id not in submitted_ids:
            result[c_id] += 1
    return result
