from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from db.courses import (
    add_course_lecturer,
    get_course_evaluations,
    get_course_lecturers,
    get_course_project_stats,
    get_pending_lecturer_evaluations_count,
    remove_course_lecturer,
)
from db.courses import create_course as db_create_course
from db.courses import get_course as db_get_course
from db.courses import get_courses as db_get_courses
from db.courses import update_course as db_update_course
from db.projects import (
    get_peer_feedback_with_users_for_projects,
    get_projects_for_course,
    get_submitted_course_evaluations_for_projects,
    get_submitted_project_evaluations,
)
from db.users import get_or_create_user
from models.course import ProjectType
from models.course_evaluation import CourseEvaluation
from models.user import User, UserRole
from schemas.courses import (
    CourseCreate,
    CourseDetail,
    CourseEvaluationPublic,
    CourseEvaluationSummary,
    CourseLecturerPublic,
    CourseListItem,
    CourseStats,
    CourseUpdate,
    CriterionScoreSummary,
    EvaluationOverviewResponse,
    ProjectEvaluationSummary,
    ProjectOverviewItem,
    ReceivedPeerFeedback,
    StudentBonusSummary,
)
from schemas.projects import AddUserBody, LecturerPublic
from services.auth import is_admin_or_course_lecturer, require_course_manage_access
from services.email import EmailSender, EmailTemplate
from settings import get_settings
from validators import derive_display_name

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
        id=require_user_id(user),
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
        submitted=ev.submitted,
        updated_at=ev.updated_at,
    )


class CoursesService:
    """Business logic for the public course endpoints.

    Assembles ``CourseListItem`` and ``CourseDetail`` responses by combining
    course rows with separate project-stats and lecturer lookups, keeping each
    DB round-trip clearly separated.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_courses(self, current_user: User | None = None) -> list[CourseListItem]:
        """Return all courses with aggregated stats for the list endpoint."""
        courses = await db_get_courses(self._session)

        course_ids = [_require_course_id(c.id) for c in courses]
        stats_by_course = await get_course_project_stats(self._session, course_ids)
        lecturers_by_course = await get_course_lecturers(self._session, course_ids)

        pending_evals_by_course: dict[int, int] = {}
        if current_user and current_user.role == UserRole.LECTURER:
            pending_evals_by_course = await get_pending_lecturer_evaluations_count(
                self._session, course_ids, current_user.id
            )

        items: list[CourseListItem] = []
        for course in courses:
            cid = _require_course_id(course.id)
            project_count, academic_years = stats_by_course.get(cid, (0, []))
            lecturer_users = lecturers_by_course.get(cid, [])

            pending_count = None
            if current_user and current_user.role == UserRole.LECTURER:
                pending_count = pending_evals_by_course.get(cid, 0)

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
                        pending_evaluations_count=pending_count,
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
        
        # Admins should only see evaluations if they are assigned lecturers
        show_evaluations = current_user is not None and current_user.id in lecturer_ids

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

        # Derive a human-readable name from the email local part when none is provided.
        resolved_name = body.name if body.name is not None else derive_display_name(body.email)
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
        EmailSender(app_env=_settings.app_env).send(
            EmailTemplate.course_invite(
                to=target_user.email,
                course_name=course.name,
                portal_url=_settings.frontend_url,
            )
        )
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

    async def get_evaluation_overview(
        self,
        course_id: int,
        *,
        year: int | None = None,
        requester: User,
    ) -> EvaluationOverviewResponse:
        """Return an aggregated evaluation overview for all projects in *course_id*.

        For each project the response includes per-criterion average scores from
        submitted lecturer evaluations, the average course-satisfaction rating from
        submitted student course evaluations, and per-student average peer bonus
        points received.

        When *year* is provided only projects from that academic year are included.
        Projects are ordered by academic year descending and project title ascending.

        Raises ``CourseNotFoundError`` when the course does not exist.
        Raises ``CoursePermissionError`` when *requester* is not an admin or an
        assigned lecturer for the course.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            raise CourseNotFoundError(f"Course {course_id} not found.")

        cid = _require_course_id(course.id)

        try:
            await require_course_manage_access(self._session, cid, requester)
        except PermissionError as exc:
            raise CoursePermissionError(str(exc)) from exc

        projects = await get_projects_for_course(self._session, cid, year=year)
        project_ids = [p.id for p in projects if p.id is not None]

        # Bulk-fetch all evaluation data in two or three queries depending on course type.
        lecturer_evals_by_project = await get_submitted_project_evaluations(
            self._session, project_ids
        )
        course_evals_by_project = await get_submitted_course_evaluations_for_projects(
            self._session, project_ids
        )
        # Peer feedback is only relevant for team courses; skip the query for individual courses.
        if course.project_type == ProjectType.TEAM:
            peer_feedback_by_project = await get_peer_feedback_with_users_for_projects(
                self._session, project_ids
            )
        else:
            peer_feedback_by_project: dict = {}

        items: list[ProjectOverviewItem] = []
        for project in projects:
            pid = project.id
            if pid is None:
                continue

            # Build per-lecturer evaluation summaries with per-criterion verbatim feedback.
            lecturer_evals = lecturer_evals_by_project.get(pid, [])
            project_evaluations = [
                ProjectEvaluationSummary(
                    lecturer_id=ev.lecturer_id,
                    criterion_scores=[
                        CriterionScoreSummary(
                            criterion_code=s["criterion_code"],
                            score=s["score"],
                            strengths=s["strengths"],
                            improvements=s["improvements"],
                        )
                        for s in ev.scores
                    ],
                )
                for ev in lecturer_evals
            ]

            # Build anonymous per-student course evaluation summaries.
            course_evaluations = [
                CourseEvaluationSummary(
                    rating=ce.rating,
                    strengths=ce.strengths,
                    improvements=ce.improvements,
                )
                for ce in course_evals_by_project.get(pid, [])
            ]

            # Aggregate per-student received peer feedback (team courses only).
            peer_fb_entries = peer_feedback_by_project.get(pid, [])
            bonus_by_student: dict[int, tuple[str, list[ReceivedPeerFeedback]]] = {}
            for feedback, receiving_user in peer_fb_entries:
                sid = feedback.receiving_student_id
                existing_name, existing_fbs = bonus_by_student.get(sid, (receiving_user.name, []))
                bonus_by_student[sid] = (
                    existing_name,
                    existing_fbs
                    + [
                        ReceivedPeerFeedback(
                            bonus_points=feedback.bonus_points,
                            strengths=feedback.strengths,
                            improvements=feedback.improvements,
                        )
                    ],
                )

            student_bonus_points = [
                StudentBonusSummary(
                    student_id=sid,
                    student_name=name,
                    feedback=feedbacks,
                )
                for sid, (name, feedbacks) in sorted(
                    bonus_by_student.items(), key=lambda kv: kv[1][0]
                )
            ]

            items.append(
                ProjectOverviewItem(
                    project_id=pid,
                    project_title=project.title,
                    academic_year=project.academic_year,
                    project_evaluations=project_evaluations,
                    course_evaluations=course_evaluations,
                    student_bonus_points=student_bonus_points,
                )
            )

        return EvaluationOverviewResponse(projects=items)
