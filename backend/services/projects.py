from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db.projects import (
    add_project_member,
    get_course_evaluations,
    get_course_lecturers,
    get_or_create_user,
    get_peer_feedback_authored,
    get_peer_feedback_received,
    get_project_evaluations,
    get_project_members,
    get_projects,
    is_course_lecturer,
    is_project_member,
    update_project,
)
from db.projects import (
    get_project as db_get_project,
)
from models.course import Course, CourseTerm
from models.course_evaluation import CourseEvaluation
from models.peer_feedback import PeerFeedback
from models.project import Project
from models.project_evaluation import ProjectEvaluation
from models.user import User, UserRole
from schemas.projects import (
    AddMemberBody,
    CourseEvaluationDetail,
    CoursePublic,
    EvaluationScoreDetail,
    LecturerPublic,
    MemberPublic,
    PeerFeedbackDetail,
    ProjectEvaluationDetail,
    ProjectPublic,
    ProjectUpdate,
)
from services.email import EmailSender, EmailTemplate
from settings import get_settings

logger = logging.getLogger(__name__)


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


def _build_project(
    p: Project,
    c: Course,
    members: list[User],
    lecturers: list[User],
    *,
    authenticated: bool = False,
    project_evaluations: list[ProjectEvaluationDetail] | None = None,
    course_evaluations: list[CourseEvaluationDetail] | None = None,
    received_peer_feedback: list[PeerFeedbackDetail] | None = None,
    authored_peer_feedback: list[PeerFeedbackDetail] | None = None,
) -> ProjectPublic:
    """Assemble a ``ProjectPublic`` response.

    When *authenticated* is ``False`` (the default), private fields — e-mails,
    ``results_unlocked``, and all evaluation collections — are omitted (``None``).
    When *authenticated* is ``True``, e-mails and ``results_unlocked`` are included
    and the optional evaluation parameters are forwarded as-is.

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
        results_unlocked=(p.results_unlocked if authenticated else None),
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
            lecturers=[
                LecturerPublic(
                    name=u.name,
                    github_alias=u.github_alias,
                    email=(u.email if authenticated else None),
                )
                for u in lecturers
            ],
        ),
        members=[
            MemberPublic(
                id=_require_id(m),
                github_alias=m.github_alias,
                name=m.name,
                email=(m.email if authenticated else None),
            )
            for m in members
        ],
        project_evaluations=(project_evaluations if authenticated else None),
        course_evaluations=(course_evaluations if authenticated else None),
        received_peer_feedback=(received_peer_feedback if authenticated else None),
        authored_peer_feedback=(authored_peer_feedback if authenticated else None),
    )


def _to_evaluation_score_detail(scores: list[dict[str, Any]]) -> list[EvaluationScoreDetail]:
    """Convert raw JSONB score dicts to ``EvaluationScoreDetail`` instances."""
    return [
        EvaluationScoreDetail(
            criterion_code=s["criterion_code"],
            score=s["score"],
            strengths=s["strengths"],
            improvements=s["improvements"],
        )
        for s in scores
    ]


def _to_project_evaluation_detail(ev: ProjectEvaluation) -> ProjectEvaluationDetail:
    """Convert a ``ProjectEvaluation`` row to its public representation."""
    return ProjectEvaluationDetail(
        lecturer_id=ev.lecturer_id,
        scores=_to_evaluation_score_detail(ev.scores),
        submitted_at=ev.submitted_at,
    )


def _to_course_evaluation_detail(ev: CourseEvaluation) -> CourseEvaluationDetail:
    """Convert a ``CourseEvaluation`` row to its public representation."""
    if ev.id is None:
        raise ValueError(f"CourseEvaluation returned from DB has no id: {ev!r}")
    return CourseEvaluationDetail(
        id=ev.id,
        student_id=ev.student_id,
        rating=ev.rating,
        strengths=ev.strengths,
        improvements=ev.improvements,
        published=ev.published,
        submitted_at=ev.submitted_at,
    )


def _to_peer_feedback_detail(feedback: PeerFeedback) -> PeerFeedbackDetail:
    """Convert a ``PeerFeedback`` row to its public representation."""
    return PeerFeedbackDetail(
        course_evaluation_id=feedback.course_evaluation_id,
        receiving_student_id=feedback.receiving_student_id,
        strengths=feedback.strengths,
        improvements=feedback.improvements,
        bonus_points=feedback.bonus_points,
    )


class PermissionDeniedError(Exception):
    """Raised when the requesting user is not authorised to modify a project."""


class ProjectNotFoundError(Exception):
    """Raised when the requested project does not exist."""


class AlreadyMemberError(Exception):
    """Raised when the target user is already a member of the project."""


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
            _build_project(
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
        return _build_project(
            p,
            c,
            members_by_project.get(p.id, []) if p.id is not None else [],
            lecturers_by_course.get(c.id, []) if c.id is not None else [],
        )

    async def get_project_detail(self, project_id: int, user: User) -> ProjectPublic | None:
        """Return an enriched ``ProjectPublic`` for an authenticated *user*.

        Includes member and lecturer e-mails and the ``results_unlocked`` flag.
        When the project has ``results_unlocked=True``, evaluation and peer-feedback
        data are attached based on the caller's role:

        * **ADMIN / LECTURER** — ``project_evaluations`` + ``course_evaluations``.
        * **STUDENT** — ``project_evaluations``, ``received_peer_feedback``, and
          ``authored_peer_feedback``.

        Returns ``None`` when no project with *project_id* exists.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            return None

        p, c = row
        project_id_list = [p.id] if p.id is not None else []
        course_id_list = [c.id] if c.id is not None else []
        members_by_project = await get_project_members(self._session, project_id_list)
        lecturers_by_course = await get_course_lecturers(self._session, course_id_list)

        project_evaluations: list[ProjectEvaluationDetail] | None = None
        course_evaluations: list[CourseEvaluationDetail] | None = None
        received_peer_feedback: list[PeerFeedbackDetail] | None = None
        authored_peer_feedback: list[PeerFeedbackDetail] | None = None

        if p.results_unlocked:
            raw_project_evaluations = await get_project_evaluations(self._session, project_id)
            project_evaluations = [
                _to_project_evaluation_detail(ev) for ev in raw_project_evaluations
            ]

            if user.role in (UserRole.ADMIN, UserRole.LECTURER):
                if c.id is not None:
                    raw_course_evaluations = await get_course_evaluations(
                        self._session, c.id, academic_year=p.academic_year
                    )
                    course_evaluations = [
                        _to_course_evaluation_detail(ev) for ev in raw_course_evaluations
                    ]
            elif user.role == UserRole.STUDENT and user.id is not None:
                raw_received_peer_feedback = await get_peer_feedback_received(
                    self._session, project_id, user.id
                )
                received_peer_feedback = [
                    _to_peer_feedback_detail(feedback) for feedback in raw_received_peer_feedback
                ]
                raw_authored_peer_feedback = await get_peer_feedback_authored(
                    self._session, project_id, user.id
                )
                authored_peer_feedback = [
                    _to_peer_feedback_detail(feedback) for feedback in raw_authored_peer_feedback
                ]

        return _build_project(
            p,
            c,
            members_by_project.get(p.id, []) if p.id is not None else [],
            lecturers_by_course.get(c.id, []) if c.id is not None else [],
            authenticated=True,
            project_evaluations=project_evaluations,
            course_evaluations=course_evaluations,
            received_peer_feedback=received_peer_feedback,
            authored_peer_feedback=authored_peer_feedback,
        )

    async def _check_write_permission(self, project_id: int, user: User) -> tuple[Project, Course]:
        """Raise ``PermissionDeniedError`` when *user* may not modify *project_id*.

        Write access is granted to:
        - Any ADMIN user (unconditional superuser access).
        - Any LECTURER who is assigned to the project's course.
        - Any user who is a member of the project.

        Non-DB sanity checks are performed first to avoid unnecessary DB load.
        Raises ``ProjectNotFoundError`` when the project does not exist so the
        caller can map it to an appropriate HTTP 404 without an extra DB query.

        Returns the ``(project, course)`` row so callers can reuse the already-fetched
        data without an additional round-trip to the database.
        """
        # Perform non-DB check before any database access.
        if user.id is None:
            raise PermissionDeniedError("User has no id.")

        row = await db_get_project(self._session, project_id)
        if row is None:
            raise ProjectNotFoundError(project_id)

        # Admins have unconditional write access to all projects.
        if user.role == UserRole.ADMIN:
            return row

        if user.role == UserRole.LECTURER:
            if await is_course_lecturer(self._session, project_id, user.id):
                return row
        if await is_project_member(self._session, project_id, user.id):
            return row

        raise PermissionDeniedError(
            f"User {user.id} is not authorised to modify project {project_id}."
        )

    async def patch_project(
        self,
        project_id: int,
        body: ProjectUpdate,
        user: User,
    ) -> ProjectPublic:
        """Apply *body* updates to the project identified by *project_id*.

        Only non-``None`` fields in *body* are written; ``None`` means "leave unchanged".
        Raises ``ProjectNotFoundError`` when the project does not exist and
        ``PermissionDeniedError`` when *user* is not a member or lecturer.
        """
        await self._check_write_permission(project_id, user)

        await update_project(
            self._session,
            project_id,
            title=body.title,
            description=body.description,
            github_url=body.github_url,
            live_url=body.live_url,
            technologies=body.technologies,
        )
        await self._session.commit()

        result = await self.get_project_detail(project_id, user)
        if result is None:
            # Should not happen — we already verified the project exists above.
            raise ProjectNotFoundError(project_id)
        return result

    async def add_member(
        self,
        project_id: int,
        body: AddMemberBody,
        user: User,
    ) -> MemberPublic:
        """Add the user identified by *body.email* as a member of *project_id*.

        If no account exists for that e-mail address a new STUDENT account is
        created.  After the DB transaction commits, a project-invitation email is
        sent via :class:`~services.email.EmailSender`.

        Raises ``ProjectNotFoundError`` when the project does not exist,
        ``PermissionDeniedError`` when *user* is not a member or lecturer, and
        ``AlreadyMemberError`` when the target user is already on the project.
        """
        # _check_write_permission returns the (project, course) row so we do not
        # need a second round-trip to fetch the project details for the email.
        project, course = await self._check_write_permission(project_id, user)

        # Default name to the local part of the email address when none is provided.
        resolved_name = body.name if body.name is not None else body.email.split("@")[0]
        target_user, created = await get_or_create_user(
            self._session,
            body.email,
            resolved_name,
            body.github_alias,
        )

        member_row, added = await add_project_member(
            self._session,
            project_id,
            target_user.id,
            invited_by=user.id,
        )
        if not added:
            raise AlreadyMemberError(
                f"User {target_user.email} is already a member of project {project_id}."
            )

        # Commit first so the member row is durable before attempting delivery.
        # Email send failures should not roll back a successful membership addition.
        await self._session.commit()

        _settings = get_settings()
        EmailSender(app_env=_settings.app_env).send(
            EmailTemplate.project_invite(
                to=body.email,
                project_name=project.title,
                course_name=course.name,
                portal_url=_settings.frontend_url,
            )
        )
        logger.info(
            "Project invitation email sent.",
            extra={"email": body.email, "project_id": project_id, "new_user": created},
        )

        return MemberPublic(
            id=target_user.id,
            github_alias=target_user.github_alias,
            name=target_user.name,
            email=target_user.email,
        )
