from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.courses import get_course as db_get_course
from db.courses import get_course_lecturers, get_course_project_stats
from db.courses import get_courses as db_get_courses
from models.user import User
from schemas.courses import CourseDetail, CourseListItem, CourseStats
from schemas.projects import LecturerPublic


def _require_course_id(course_id: int | None) -> int:
    """Return ``course_id``, raising ``ValueError`` if it is ``None``.

    Courses returned from the database always have a non-None primary key.
    This helper surfaces the inconsistency early with a clear message.
    """
    if course_id is None:
        raise ValueError("Course returned from DB has no id.")
    return course_id


def _lecturer_public(user: User) -> LecturerPublic:
    """Build a ``LecturerPublic`` from a ``User`` row."""
    return LecturerPublic(name=user.name, github_alias=user.github_alias)


class CoursesService:
    """Business logic for the public course endpoints.

    Assembles ``CourseListItem`` and ``CourseDetail`` responses by combining
    course rows with separate project-stats and lecturer lookups, keeping each
    DB round-trip clearly separated.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_courses(self) -> list[CourseListItem]:
        """Return all courses with aggregated stats for the list endpoint."""
        courses = await db_get_courses(self._session)

        course_ids = [_require_course_id(c.id) for c in courses]
        stats_by_course = await get_course_project_stats(self._session, course_ids)
        lecturers_by_course = await get_course_lecturers(self._session, course_ids)

        items: list[CourseListItem] = []
        for course in courses:
            cid = _require_course_id(course.id)
            project_count, academic_years = stats_by_course.get(cid, (0, []))
            lecturer_users = lecturers_by_course.get(cid, [])
            items.append(
                CourseListItem(
                    id=cid,
                    code=course.code,
                    name=course.name,
                    stats=CourseStats(
                        project_count=project_count,
                        academic_years=academic_years,
                        lecturer_names=sorted(u.name for u in lecturer_users),
                    ),
                )
            )
        return items

    async def get_course(self, course_id: int) -> CourseDetail | None:
        """Return the full public detail of the course with ``course_id``.

        Returns ``None`` when no course with the given id exists.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            return None

        cid = _require_course_id(course.id)
        lecturers_by_course = await get_course_lecturers(self._session, [cid])
        lecturer_users = lecturers_by_course.get(cid, [])

        return CourseDetail(
            id=cid,
            code=course.code,
            name=course.name,
            syllabus=course.syllabus,
            term=course.term,
            project_type=course.project_type,
            min_score=course.min_score,
            peer_bonus_budget=course.peer_bonus_budget,
            evaluation_criteria=course.evaluation_criteria,
            links=course.links,
            lecturers=[_lecturer_public(u) for u in lecturer_users],
        )
