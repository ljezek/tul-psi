from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.course_evaluation import CourseEvaluation
from models.course_lecturer import CourseLecturer
from models.project import Project
from models.user import User


async def get_courses(session: AsyncSession) -> list[Course]:
    """Return all courses ordered by course code."""
    stmt = select(Course).order_by(Course.code)
    return list((await session.execute(stmt)).scalars().all())


async def get_course(session: AsyncSession, course_id: int) -> Course | None:
    """Return the course with the given ``course_id``, or ``None`` if not found."""
    stmt = select(Course).where(Course.id == course_id)
    return (await session.execute(stmt)).scalars().first()


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
    Both draft and published evaluations are returned so that admin and lecturer
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
