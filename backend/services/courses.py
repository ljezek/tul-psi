from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.courses import get_course as db_get_course
from db.courses import get_course_evaluations, get_course_lecturers, get_course_project_stats
from db.courses import get_courses as db_get_courses
from models.course_evaluation import CourseEvaluation
from models.user import User
from schemas.courses import CourseDetail, CourseEvaluationPublic, CourseListItem, CourseStats
from schemas.projects import LecturerPublic
from services.auth import is_admin_or_course_lecturer


def _require_course_id(course_id: int | None) -> int:
    """Return ``course_id``, raising ``ValueError`` if it is ``None``.

    Courses returned from the database always have a non-None primary key.
    This helper surfaces the inconsistency early with a clear message.
    """
    if course_id is None:
        raise ValueError("Course returned from DB has no id.")
    return course_id


def _lecturer_public(user: User, *, include_email: bool) -> LecturerPublic:
    """Build a ``LecturerPublic`` from a ``User`` row.

    ``email`` is included when ``include_email`` is ``True``, which should
    only be the case when the requesting user holds a valid session.
    """
    return LecturerPublic(
        name=user.name,
        github_alias=user.github_alias,
        email=user.email if include_email else None,
    )


def _course_evaluation_public(ev: CourseEvaluation) -> CourseEvaluationPublic:
    """Build a ``CourseEvaluationPublic`` from a ``CourseEvaluation`` row."""
    if ev.id is None:
        raise ValueError(f"CourseEvaluation returned from DB has no id: {ev!r}")
    return CourseEvaluationPublic(
        id=ev.id,
        project_id=ev.project_id,
        student_id=ev.student_id,
        rating=ev.rating,
        strengths=ev.strengths,
        improvements=ev.improvements,
        published=ev.published,
        submitted_at=ev.submitted_at,
    )


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
                    syllabus=course.syllabus,
                    lecturer_names=sorted(u.name for u in lecturer_users),
                    stats=CourseStats(
                        project_count=project_count,
                        academic_years=academic_years,
                    ),
                )
            )
        return items

    async def get_course(
        self,
        course_id: int,
        current_user: User | None = None,
    ) -> CourseDetail | None:
        """Return the full public detail of the course with ``course_id``.

        Returns ``None`` when no course with the given id exists.

        ``current_user`` controls two optional enrichments:
        - Lecturer e-mail addresses are included when any authenticated user requests the detail.
        - ``course_evaluations`` are populated only for admin users and for lecturers
          assigned to this course.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            return None

        cid = _require_course_id(course.id)
        lecturers_by_course = await get_course_lecturers(self._session, [cid])
        lecturer_users = lecturers_by_course.get(cid, [])

        include_email = current_user is not None
        lecturer_ids = {u.id for u in lecturer_users if u.id is not None}
        show_evaluations = is_admin_or_course_lecturer(current_user, lecturer_ids)

        course_evaluations: list[CourseEvaluationPublic] | None = None
        if show_evaluations:
            raw = await get_course_evaluations(self._session, cid)
            course_evaluations = [_course_evaluation_public(ev) for ev in raw]

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
            lecturers=[_lecturer_public(u, include_email=include_email) for u in lecturer_users],
            course_evaluations=course_evaluations,
        )
