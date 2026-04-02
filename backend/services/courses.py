from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from db.courses import (
    add_course_lecturer,
    get_course_evaluations,
    get_course_lecturers,
    get_course_project_stats,
    remove_course_lecturer,
)
from db.courses import create_course as db_create_course
from db.courses import get_course as db_get_course
from db.courses import get_courses as db_get_courses
from db.courses import update_course as db_update_course
from db.projects import get_or_create_user
from models.course_evaluation import CourseEvaluation
from models.user import User, UserRole
from schemas.courses import (
    CourseCreate,
    CourseDetail,
    CourseEvaluationPublic,
    CourseLecturerPublic,
    CourseListItem,
    CourseStats,
    CourseUpdate,
)
from schemas.projects import AddUserBody, LecturerPublic
from services.auth import is_admin_or_course_lecturer, require_course_manage_access
from services.email import EmailDeliveryNotImplementedError, EmailSender, EmailTemplate
from settings import get_settings

logger = logging.getLogger(__name__)


class CoursePermissionError(Exception):
    """Raised when a user lacks the permission to create or modify a course."""


class CourseNotFoundError(Exception):
    """Raised when a course with the requested id does not exist."""


class CourseLecturerAlreadyAssignedError(Exception):
    """Raised when a lecturer is already assigned to the course."""


class CourseLecturerNotAssignedError(Exception):
    """Raised when trying to remove a lecturer who is not assigned to the course."""


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

    async def create_course(
        self,
        data: CourseCreate,
        current_user: User,
    ) -> CourseDetail:
        """Create a new course and return its full detail.

        Only admins are allowed to create courses.  Raises
        ``CoursePermissionError`` if ``current_user`` is not an admin.

        After inserting the row the session is committed so that the new
        course is immediately visible to subsequent queries.
        """
        if current_user.role != UserRole.ADMIN:
            raise CoursePermissionError("Only admins can create courses.")

        created_by = current_user.id
        course = await db_create_course(self._session, data, created_by)
        await self._session.commit()

        # Fetch the full detail (includes lecturers list — empty for a new course).
        cid = _require_course_id(course.id)
        result = await self.get_course(cid, current_user=current_user)
        if result is None:
            raise ValueError(f"Newly created course {cid} could not be retrieved.")
        return result

    async def update_course(
        self,
        course_id: int,
        data: CourseUpdate,
        current_user: User,
    ) -> CourseDetail | None:
        """Apply a partial update to the course identified by ``course_id``.

        Returns ``None`` when no course with the given id exists.

        Access is restricted to admins and to lecturers who are currently
        assigned to the course.  Raises ``CoursePermissionError`` for any
        other authenticated role or for a lecturer not assigned to this
        course.

        Only fields explicitly provided in the request body are modified;
        omitted fields keep their existing values.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            return None

        try:
            await require_course_manage_access(self._session, course_id, current_user)
        except PermissionError as exc:
            raise CoursePermissionError(str(exc)) from exc

        await db_update_course(self._session, course, data)
        await self._session.commit()

        result = await self.get_course(course_id, current_user=current_user)
        if result is None:
            raise ValueError(f"Course {course_id} disappeared after update.")
        return result

    async def add_lecturer(
        self,
        course_id: int,
        body: AddUserBody,
        current_user: User,
    ) -> CourseLecturerPublic:
        """Assign the user identified by *body.email* as a lecturer on *course_id*.

        If no account exists for that e-mail address a new LECTURER account is
        created.  A login-link notification is sent to the user via email.

        Raises ``CourseNotFoundError`` when no course with the given id exists,
        ``CoursePermissionError`` when *current_user* is not an admin or
        an assigned lecturer on the course, and ``CourseLecturerAlreadyAssignedError``
        when the target user is already a lecturer on this course.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            raise CourseNotFoundError(f"Course {course_id} not found.")

        try:
            await require_course_manage_access(self._session, course_id, current_user)
        except PermissionError as exc:
            raise CoursePermissionError(str(exc)) from exc

        # Default name to the local part of the email address when none is provided.
        resolved_name = body.name if body.name is not None else body.email.split("@")[0]
        target_user, created = await get_or_create_user(
            self._session,
            body.email,
            resolved_name,
            body.github_alias,
            role=UserRole.LECTURER,
        )

        if target_user.id is None:
            raise ValueError(f"User returned from DB has no id after flush: {target_user!r}")

        added = await add_course_lecturer(self._session, course_id, target_user.id)
        if not added:
            raise CourseLecturerAlreadyAssignedError(
                f"User {target_user.email} is already a lecturer on course {course_id}."
            )

        # Commit first so the lecturer assignment is durable before attempting delivery.
        # Email send failures should not roll back a successful assignment.
        await self._session.commit()

        _settings = get_settings()
        try:
            EmailSender(app_env=_settings.app_env).send(
                EmailTemplate.course_invite(
                    to=target_user.email,
                    course_name=course.name,
                    portal_url=_settings.frontend_url,
                )
            )
        except NotImplementedError as exc:
            logger.error(
                "Email sending is not implemented in the current environment; "
                "lecturer assigned but invite email not delivered.",
                extra={"email": target_user.email, "course_id": course_id},
            )
            raise EmailDeliveryNotImplementedError(
                "Email delivery is not configured for this environment."
            ) from exc
        logger.info(
            "Course invite email sent.",
            extra={"email": target_user.email, "course_id": course_id, "new_user": created},
        )

        return CourseLecturerPublic(
            id=target_user.id,
            name=target_user.name,
            github_alias=target_user.github_alias,
            email=target_user.email,
        )

    async def remove_lecturer(
        self,
        course_id: int,
        user_id: int,
        current_user: User,
    ) -> None:
        """Remove the lecturer assignment for *user_id* from *course_id*.

        Raises ``CourseNotFoundError`` when no course with the given id exists,
        ``CoursePermissionError`` when *current_user* is not an admin or
        an assigned lecturer on the course, and ``CourseLecturerNotAssignedError``
        when no such assignment exists.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            raise CourseNotFoundError(f"Course {course_id} not found.")

        try:
            await require_course_manage_access(self._session, course_id, current_user)
        except PermissionError as exc:
            raise CoursePermissionError(str(exc)) from exc

        deleted = await remove_course_lecturer(self._session, course_id, user_id)
        if not deleted:
            raise CourseLecturerNotAssignedError(
                f"User {user_id} is not a lecturer on course {course_id}."
            )

        await self._session.commit()
