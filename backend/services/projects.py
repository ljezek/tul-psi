from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db.auth import get_or_create_user
from db.courses import get_course as db_get_course
from db.courses import get_course_lecturers
from db.projects import (
    add_project_member,
    get_all_peer_feedback_for_project,
    get_all_peer_feedback_for_projects,
    get_course_evaluation_by_student,
    get_course_evaluations,
    get_course_evaluations_for_student,
    get_evaluation_counts_for_projects,
    get_lecturer_evaluation_statuses,
    get_member_evaluation_statuses,
    get_peer_feedback_authored,
    get_peer_feedback_received,
    get_project_evaluation_by_lecturer,
    get_project_evaluations,
    get_project_evaluations_by_lecturer_for_projects,
    get_project_evaluations_for_projects,
    get_project_members,
    get_projects,
    is_course_lecturer,
    is_project_member,
    replace_peer_feedback,
    update_project,
    upsert_course_evaluation,
)
from db.projects import (
    create_project as db_create_project,
)
from db.projects import (
    delete_project as db_delete_project,
)
from db.projects import (
    get_project as db_get_project,
)
from db.projects import (
    lock_project_results as db_lock_project_results,
)
from db.projects import (
    unlock_project_results as db_unlock_project_results,
)
from db.projects import (
    upsert_project_evaluation as db_upsert_project_evaluation,
)
from models.course import Course, CourseTerm, ProjectType
from models.course_evaluation import CourseEvaluation
from models.peer_feedback import PeerFeedback
from models.project import Project
from models.project_evaluation import ProjectEvaluation
from models.user import User, UserRole
from schemas.projects import (
    AddMemberBody,
    CourseEvaluationDetail,
    CourseEvaluationFormResponse,
    CourseEvaluationUpsert,
    CoursePublic,
    EvaluationScoreDetail,
    LecturerPublic,
    MemberPublic,
    PeerFeedbackDetail,
    ProjectCreate,
    ProjectEvaluationCreate,
    ProjectEvaluationDetail,
    ProjectPublic,
    ProjectUpdate,
)
from services.auth import require_course_lecturer_access, require_course_manage_access
from services.email import EmailSender, EmailTemplate
from settings import get_settings
from validators import derive_display_name, require_user_id

logger = logging.getLogger(__name__)


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
    submitted_lecturer_count: int | None = None,
    submitted_student_count: int | None = None,
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

    total_points: float | None = None
    if p.results_unlocked and authenticated:
        # Total points = Lecturer avg + Peer avg (bonus)
        lecturer_avg = 0.0
        if project_evaluations:
            # Group by criterion to get averages
            criterion_scores: dict[str, list[int]] = {}
            for ev in project_evaluations:
                for score in ev.scores:
                    criterion_scores.setdefault(score.criterion_code, []).append(score.score)

            for scores in criterion_scores.values():
                if scores:
                    lecturer_avg += sum(scores) / len(scores)

        peer_avg = 0.0
        if received_peer_feedback:
            peer_avg = sum(f.bonus_points for f in received_peer_feedback) / len(
                received_peer_feedback
            )

        total_points = lecturer_avg + peer_avg

    return ProjectPublic(
        id=p.id,
        title=p.title,
        description=p.description,
        github_url=p.github_url,
        live_url=p.live_url,
        technologies=p.technologies,
        academic_year=p.academic_year,
        results_unlocked=(p.results_unlocked if authenticated else None),
        submitted_lecturer_count=(submitted_lecturer_count if authenticated else None),
        submitted_student_count=(submitted_student_count if authenticated else None),
        course=CoursePublic(
            id=c.id,
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
                    id=require_user_id(u),
                    name=u.name,
                    github_alias=u.github_alias,
                    email=(u.email if authenticated else None),
                )
                for u in lecturers
            ],
        ),
        members=[
            MemberPublic(
                id=require_user_id(m),
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
        total_points=(total_points if authenticated else None),
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
        updated_at=ev.updated_at,
        submitted=ev.submitted,
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
        submitted=ev.submitted,
        updated_at=ev.updated_at,
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


class EvaluationConflictError(Exception):
    """Raised when a project evaluation cannot be created or updated due to a conflict.

    This occurs when the project results are already unlocked, preventing any
    further changes to submitted evaluations.
    """


class InvalidEvaluationDataError(Exception):
    """Raised when submitted evaluation data fails domain-level validation.

    Examples: criterion code not found in the course config, or a score value
    exceeding the configured maximum for that criterion.  Maps to HTTP 422 at
    the API layer.
    """


async def _check_and_auto_unlock_project(
    session: AsyncSession,
    project_id: int,
) -> None:
    """Automatically unlock project results when all evaluations are complete.

    The unlock fires when **both** of the following conditions are satisfied:

    * Every lecturer currently assigned to the project's course has submitted a
      ``ProjectEvaluation`` (``submitted=True``).
    * Every project member has submitted a ``CourseEvaluation`` (``submitted=True``).

    Uses two JOIN queries (rather than five separate count queries) to obtain both
    the participant list and their submission status in one round-trip each.  If
    either list is empty (no lecturers or no members) the condition is not considered
    met and the project is left locked.  When the condition is met, results are
    unlocked and a notification email is sent to every participant (students and
    lecturers alike).  The caller is responsible for committing the session after
    this call when an unlock occurs.
    """
    row = await db_get_project(session, project_id)
    if row is None:
        return

    p, course = row
    if course.id is None:
        return

    # Each query performs a LEFT JOIN to return every assigned participant together
    # with their submission flag, reducing what was previously five separate queries
    # down to three (including the project lookup above).
    lecturer_statuses = await get_lecturer_evaluation_statuses(session, project_id, course.id)
    member_statuses = await get_member_evaluation_statuses(session, project_id)

    if not lecturer_statuses or not member_statuses:
        # Not enough participants to determine completion.
        return

    all_lecturers_submitted = all(submitted for _, submitted in lecturer_statuses)
    all_members_submitted = all(submitted for _, submitted in member_statuses)

    if not all_lecturers_submitted or not all_members_submitted:
        return

    await db_unlock_project_results(session, project_id)

    # Send a notification email to every participant now that results are visible.
    peer_feedback_enabled = course.peer_bonus_budget is not None
    _settings = get_settings()
    sender = EmailSender(app_env=_settings.app_env)
    participants: list[User] = [u for u, _ in lecturer_statuses] + [u for u, _ in member_statuses]
    for participant in participants:
        if participant.email is None:
            continue
        sender.send(
            EmailTemplate.results_unlocked(
                to=participant.email,
                project_name=p.title,
                portal_url=_settings.frontend_url,
                peer_feedback_enabled=peer_feedback_enabled,
            )
        )
    logger.info(
        "Project results unlocked and notification emails sent.",
        extra={
            "project_id": project_id,
            "recipients": [u.email for u in participants if u.email is not None],
        },
    )


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
        user: User | None = None,
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

        # If an authenticated user is provided, fetch their evaluations for these projects.
        # We only need to check projects where the user is actually a member.
        user_evals: dict[int, CourseEvaluationDetail] = {}
        eval_counts: dict[int, tuple[int, int]] = {}
        if user is not None and user.id is not None:
            eval_counts = await get_evaluation_counts_for_projects(self._session, project_ids)
            member_project_ids = [
                pid
                for pid in project_ids
                if any(m.id == user.id for m in members_by_project.get(pid, []))
            ]
            if member_project_ids:
                raw_user_evals = await get_course_evaluations_for_student(
                    self._session, member_project_ids, user.id
                )
                user_evals = {
                    pid: _to_course_evaluation_detail(ev) for pid, ev in raw_user_evals.items()
                }

        # For member projects with unlocked results, we need lecturer and peer feedback
        # to calculate total_points for the dashboard.
        # For lecturers, we want to see their own evaluations even if not unlocked.
        project_evals: dict[int, list[ProjectEvaluationDetail]] = {}
        peer_feedback: dict[int, list[PeerFeedbackDetail]] = {}
        if user is not None and user.id is not None:
            member_project_ids = [
                pid
                for pid in project_ids
                if any(m.id == user.id for m in members_by_project.get(pid, []))
            ]
            unlocked_member_project_ids = [
                pid
                for pid, p_obj in {p.id: p for p, _ in rows}.items()
                if pid in member_project_ids and p_obj.results_unlocked
            ]
            if unlocked_member_project_ids:
                # Bulk fetch for members
                raw_pevals_map = await get_project_evaluations_for_projects(
                    self._session, unlocked_member_project_ids
                )
                for pid, evs in raw_pevals_map.items():
                    project_evals[pid] = [_to_project_evaluation_detail(ev) for ev in evs]

                raw_pfeedback_map = await get_all_peer_feedback_for_projects(
                    self._session, unlocked_member_project_ids
                )
                for pid, fbs in raw_pfeedback_map.items():
                    peer_feedback[pid] = [_to_peer_feedback_detail(fb) for fb in fbs]

            # 2. Lecturer logic: fetch evaluations for projects where user is a lecturer
            if user.role in (UserRole.ADMIN, UserRole.LECTURER):
                # Identify which projects the user is a lecturer for
                lecturer_project_ids = []
                for p, c in rows:
                    if p.id is not None and c.id is not None:
                        # Check if user is in lecturers_by_course[c.id]
                        if any(lect.id == user.id for lect in lecturers_by_course.get(c.id, [])):
                            lecturer_project_ids.append(p.id)

                if lecturer_project_ids:
                    # Bulk fetch for lecturers
                    raw_lecturer_pevals_map = (
                        await get_project_evaluations_by_lecturer_for_projects(
                            self._session, lecturer_project_ids, user.id
                        )
                    )
                    for pid, ev in raw_lecturer_pevals_map.items():
                        # Fetch peer feedback if results are unlocked for these lecturer projects.
                        p_obj = next((p for p, _ in rows if p.id == pid), None)
                        if p_obj and p_obj.results_unlocked:
                            # Results are unlocked: lecturers see EVERYTHING
                            if pid not in project_evals:
                                raw_all_pevals = await get_project_evaluations(self._session, pid)
                                project_evals[pid] = [
                                    _to_project_evaluation_detail(ev) for ev in raw_all_pevals
                                ]

                            if pid not in peer_feedback:
                                raw_pfeedback = await get_all_peer_feedback_for_project(
                                    self._session, pid
                                )
                                peer_feedback[pid] = [
                                    _to_peer_feedback_detail(fb) for fb in raw_pfeedback
                                ]
                        else:
                            # Results locked: lecturer only sees their own draft/submission
                            if pid not in project_evals:
                                project_evals[pid] = [_to_project_evaluation_detail(ev)]

        return [
            _build_project(
                p,
                c,
                members_by_project.get(p.id, []) if p.id is not None else [],
                lecturers_by_course.get(c.id, []) if c.id is not None else [],
                authenticated=(user is not None),
                project_evaluations=project_evals.get(p.id) if p.id is not None else None,
                course_evaluations=[user_evals[p.id]] if p.id in user_evals else [],
                received_peer_feedback=peer_feedback.get(p.id, [])
                if user is not None and user.role in (UserRole.ADMIN, UserRole.LECTURER)
                else [
                    fb
                    for fb in peer_feedback.get(p.id, [])
                    if user is not None and fb.receiving_student_id == user.id
                ]
                if p.id is not None
                else None,
                submitted_lecturer_count=eval_counts.get(p.id, (0, 0))[0]
                if p.id is not None
                else 0,
                submitted_student_count=eval_counts.get(p.id, (0, 0))[1] if p.id is not None else 0,
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
        eval_counts = await get_evaluation_counts_for_projects(self._session, project_id_list)

        return _build_project(
            p,
            c,
            members_by_project.get(p.id, []) if p.id is not None else [],
            lecturers_by_course.get(c.id, []) if c.id is not None else [],
            submitted_lecturer_count=eval_counts.get(p.id, (0, 0))[0] if p.id is not None else 0,
            submitted_student_count=eval_counts.get(p.id, (0, 0))[1] if p.id is not None else 0,
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

        project, course = row
        project_id_list = [project.id] if project.id is not None else []
        course_id_list = [course.id] if course.id is not None else []
        members_by_project = await get_project_members(self._session, project_id_list)
        lecturers_by_course = await get_course_lecturers(self._session, course_id_list)
        eval_counts = await get_evaluation_counts_for_projects(self._session, project_id_list)

        lecturers = lecturers_by_course.get(course.id, []) if course.id is not None else []
        lecturer_ids = [l.id for l in lecturers if l.id is not None]

        # Admins only see evaluations if they are assigned as lecturers
        show_evaluations = user.id in lecturer_ids

        project_evaluations: list[ProjectEvaluationDetail] | None = None

        course_evaluations: list[CourseEvaluationDetail] | None = None
        received_peer_feedback: list[PeerFeedbackDetail] | None = None
        authored_peer_feedback: list[PeerFeedbackDetail] | None = None

        if project.results_unlocked:
            raw_project_evaluations = await get_project_evaluations(self._session, project_id)
            project_evaluations = [
                _to_project_evaluation_detail(ev) for ev in raw_project_evaluations
            ]

            if user.role in (UserRole.ADMIN, UserRole.LECTURER):
                if course.id is not None:
                    raw_course_evaluations = await get_course_evaluations(
                        self._session, course.id, academic_year=project.academic_year
                    )
                    course_evaluations = [
                        _to_course_evaluation_detail(ev) for ev in raw_course_evaluations
                    ]

                # Fetch ALL peer feedback for the project
                raw_received_peer_feedback = await get_all_peer_feedback_for_project(
                    self._session, project_id
                )
                received_peer_feedback = [
                    _to_peer_feedback_detail(feedback) for feedback in raw_received_peer_feedback
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

        # Students always see their own course evaluation status (draft or submitted)
        # only if they are members of the project.
        if user.role == UserRole.STUDENT and user.id is not None:
            members = members_by_project.get(project.id, [])
            is_member = any(m.id == user.id for m in members)
            if is_member:
                raw_my_eval = await get_course_evaluation_by_student(
                    self._session, project_id, user.id
                )
                if raw_my_eval:
                    course_evaluations = [_to_course_evaluation_detail(raw_my_eval)]

        return _build_project(
            project,
            course,
            members_by_project.get(project.id, []) if project.id is not None else [],
            lecturers_by_course.get(course.id, []) if course.id is not None else [],
            authenticated=True,
            project_evaluations=project_evaluations,
            course_evaluations=course_evaluations,
            received_peer_feedback=received_peer_feedback,
            authored_peer_feedback=authored_peer_feedback,
            submitted_lecturer_count=eval_counts.get(project.id, (0, 0))[0] if project.id is not None else 0,
            submitted_student_count=eval_counts.get(project.id, (0, 0))[1] if project.id is not None else 0,
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

        # Derive a human-readable name from the email local part when none is provided.
        resolved_name = body.name if body.name is not None else derive_display_name(body.email)
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

    async def create_project(
        self,
        course_id: int,
        data: ProjectCreate,
        requester: User,
    ) -> ProjectPublic:
        """Create a new project for the course identified by *course_id*.

        Raises ``LookupError`` when the course does not exist.
        Raises ``PermissionError`` when *requester* is not an admin or assigned lecturer.

        When ``data.owner_email`` is set, the system looks up (or creates) a
        ``STUDENT`` account and adds it as the initial project member.  A fake
        invite email is logged to simulate the notification workflow.

        Returns the assembled ``ProjectPublic`` for the newly created project.
        """
        course = await db_get_course(self._session, course_id)
        if course is None:
            raise LookupError(f"Course {course_id} not found.")

        if course.id is None:
            raise ValueError(f"Course returned from DB has no id: {course!r}")

        await require_course_manage_access(self._session, course.id, requester)

        project = await db_create_project(
            self._session,
            course_id=course.id,
            title=data.title,
            description=data.description,
            github_url=data.github_url,
            live_url=data.live_url,
            technologies=data.technologies,
            academic_year=data.academic_year,
        )

        if data.owner_email is not None:
            # Name derivation is handled inside get_or_create_user when name is None.
            owner_user, _ = await get_or_create_user(
                self._session,
                data.owner_email,
            )
            if project.id is None:
                raise ValueError(f"Project returned from DB has no id: {project!r}")
            if owner_user.id is None:
                raise ValueError(f"Owner user returned from DB has no id: {owner_user!r}")
            await add_project_member(
                self._session,
                project.id,
                owner_user.id,
                invited_by=require_user_id(requester),
            )

        # Commit the project and member rows before attempting email delivery.
        # A send failure must not roll back a successfully created project.
        await self._session.commit()
        await self._session.refresh(project)

        if data.owner_email is not None:
            _settings = get_settings()
            EmailSender(app_env=_settings.app_env).send(
                EmailTemplate.project_invite(
                    to=data.owner_email,
                    project_name=project.title,
                    course_name=course.name,
                    portal_url=_settings.frontend_url,
                )
            )
            logger.info(
                "Project invite email sent.",
                extra={"recipient_email": data.owner_email, "project_id": project.id},
            )

        if project.id is None:
            raise ValueError(f"Project returned from DB has no id after commit: {project!r}")
        detail = await self.get_project_detail(project.id, requester)
        if detail is None:
            raise RuntimeError(
                "get_project_detail unexpectedly returned None for newly created"
                f" project {project.id}."
            )
        return detail

    async def delete_project(self, project_id: int, requester: User) -> None:
        """Delete the project identified by *project_id*.

        Raises ``LookupError`` when the project does not exist.
        Raises ``PermissionError`` when *requester* is not an admin or assigned lecturer.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            raise LookupError(f"Project {project_id} not found.")

        _p, course = row
        if course.id is None:
            raise ValueError(f"Course returned from DB has no id: {course!r}")

        await require_course_manage_access(self._session, course.id, requester)
        await db_delete_project(self._session, project_id)
        await self._session.commit()

    async def unlock_project(self, project_id: int, requester: User) -> ProjectPublic:
        """Set ``results_unlocked=True`` on the project identified by *project_id*.

        Raises ``LookupError`` when the project does not exist.
        Raises ``PermissionError`` when *requester* is not an admin or assigned lecturer.

        Returns the updated ``ProjectPublic``.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            raise LookupError(f"Project {project_id} not found.")

        _p, course = row
        if course.id is None:
            raise ValueError(f"Course returned from DB has no id: {course!r}")

        await require_course_manage_access(self._session, course.id, requester)
        await db_unlock_project_results(self._session, project_id)
        await self._session.commit()

        return await self.get_project_detail(project_id, requester)

    async def lock_project(self, project_id: int, requester: User) -> ProjectPublic:
        """Set ``results_unlocked=False`` on the project identified by *project_id*.

        Raises ``LookupError`` when the project does not exist.
        Raises ``PermissionError`` when *requester* is not an admin or assigned lecturer.

        Returns the updated ``ProjectPublic``.
        """
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("service.lock_project") as span:
            span.set_attribute("project_id", project_id)
            span.set_attribute("requester_id", requester.id or 0)

            row = await db_get_project(self._session, project_id)
            if row is None:
                raise LookupError(f"Project {project_id} not found.")

            _p, course = row
            if course.id is None:
                raise ValueError(f"Course returned from DB has no id: {course!r}")

            await require_course_manage_access(self._session, course.id, requester)
            await lock_project_results(self._session, project_id)
            await self._session.commit()

            return await self.get_project_detail(project_id, requester)

    async def get_project_evaluation(
        self,
        project_id: int,
        requester: User,
    ) -> ProjectEvaluationDetail:
        """Return the calling lecturer's evaluation for *project_id*.

        Raises ``LookupError`` when the project does not exist or no evaluation
        row exists for the calling lecturer on this project.
        Raises ``PermissionError`` when *requester* is not an admin or assigned lecturer.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            raise LookupError(f"Project {project_id} not found.")

        _p, course = row
        if course.id is None:
            raise ValueError(f"Course returned from DB has no id: {course!r}")

        await require_course_manage_access(self._session, course.id, requester)

        requester_id = require_user_id(requester)

        evaluation = await get_project_evaluation_by_lecturer(
            self._session, project_id, requester_id
        )
        if evaluation is None:
            raise LookupError(
                f"No evaluation found for lecturer {requester_id} on project {project_id}."
            )
        return _to_project_evaluation_detail(evaluation)

    async def save_project_evaluation(
        self,
        project_id: int,
        body: ProjectEvaluationCreate,
        requester: User,
    ) -> ProjectEvaluationDetail:
        """Create or update the calling lecturer's evaluation for *project_id*.

        Draft saves (``body.submitted=False``) create or overwrite the evaluation
        row without triggering the auto-unlock check.  Final submissions
        (``body.submitted=True``) additionally call
        ``_check_and_auto_unlock_project`` so that results are unlocked
        automatically once all lecturers and students have submitted.

        Only users explicitly assigned as lecturers for the course may call this
        method.  Unlike general course-management actions, admin users who are
        not assigned as course lecturers are denied access — a project evaluation
        is a per-lecturer artefact and should only be created by lecturers on
        the course.

        Raises ``LookupError`` when the project does not exist.
        Raises ``PermissionError`` when *requester* is not an assigned lecturer for
        the project's course (admin users without a lecturer assignment are also
        denied).
        Raises ``EvaluationConflictError`` when the project results are already
        unlocked (editing is no longer permitted after unlock).
        Raises ``InvalidEvaluationDataError`` when any ``criterion_code`` is not
        configured for the course or any ``score`` exceeds the criterion's
        ``max_score``.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            raise LookupError(f"Project {project_id} not found.")

        p, course = row
        if course.id is None:
            raise ValueError(f"Course returned from DB has no id: {course!r}")

        # Use the strict lecturer check: admin users who are not assigned to the
        # course are denied, because evaluations are per-lecturer artefacts.
        await require_course_lecturer_access(self._session, course.id, requester)

        if p.results_unlocked:
            raise EvaluationConflictError(
                f"Project {project_id} results are already unlocked; evaluation cannot be edited."
            )

        # Validate criterion codes and score ranges against the course configuration.
        criterion_max_scores = {c["code"]: c["max_score"] for c in course.evaluation_criteria}
        submitted_codes = {s.criterion_code for s in body.scores}
        invalid_codes = submitted_codes - set(criterion_max_scores)
        if invalid_codes:
            raise InvalidEvaluationDataError(
                f"Invalid criterion code(s) for course {course.code}: {sorted(invalid_codes)}."
            )
        for submitted_score in body.scores:
            max_score = criterion_max_scores[submitted_score.criterion_code]
            if submitted_score.score < 0 or submitted_score.score > max_score:
                raise InvalidEvaluationDataError(
                    f"Invalid score for criterion {submitted_score.criterion_code!r}"
                    f" in course {course.code}: {submitted_score.score}."
                    f" Allowed range is 0 to {max_score}."
                )

        requester_id = require_user_id(requester)

        scores_dicts = [
            {
                "criterion_code": s.criterion_code,
                "score": s.score,
                "strengths": s.strengths,
                "improvements": s.improvements,
            }
            for s in body.scores
        ]

        evaluation = await db_upsert_project_evaluation(
            self._session,
            project_id,
            requester_id,
            scores_dicts,
            submitted=body.submitted,
        )
        await self._session.commit()

        if body.submitted:
            await _check_and_auto_unlock_project(self._session, project_id)
            await self._session.commit()

        return _to_project_evaluation_detail(evaluation)

    async def get_course_evaluation_form(
        self,
        project_id: int,
        user: User,
    ) -> CourseEvaluationFormResponse:
        """Return all data a student needs to render the course-evaluation form.

        Includes the list of teammates (members excluding the caller), the
        course's peer-bonus budget, the caller's current draft evaluation
        (if any), and the peer-feedback entries the caller has authored.

        Raises ``ProjectNotFoundError`` when the project does not exist.
        Raises ``PermissionDeniedError`` when *user* is not a student or is
        not a project member.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            raise ProjectNotFoundError(project_id)

        p, course = row
        user_id = require_user_id(user)

        if user.role != UserRole.STUDENT:
            raise PermissionDeniedError("Only students may access the course evaluation form.")

        if not await is_project_member(self._session, project_id, user_id):
            raise PermissionDeniedError(f"User {user_id} is not a member of project {project_id}.")

        # For team courses, build the teammates list from project members.
        # Individual projects have a single student member, so there are no teammates.
        teammates: list[MemberPublic] = []
        if course.project_type == ProjectType.TEAM:
            members_by_project = await get_project_members(self._session, [project_id])
            all_members = members_by_project.get(project_id, [])
            teammates = [
                MemberPublic(
                    id=require_user_id(m),
                    github_alias=m.github_alias,
                    name=m.name,
                    email=m.email,
                )
                for m in all_members
                if m.id != user_id
            ]

        current_eval = await get_course_evaluation_by_student(self._session, project_id, user_id)
        current_evaluation: CourseEvaluationDetail | None = None
        authored_peer_feedback: list[PeerFeedbackDetail] = []

        if current_eval is not None:
            current_evaluation = _to_course_evaluation_detail(current_eval)
            raw_authored = await get_peer_feedback_authored(self._session, project_id, user_id)
            authored_peer_feedback = [_to_peer_feedback_detail(fb) for fb in raw_authored]

        return CourseEvaluationFormResponse(
            teammates=teammates,
            peer_bonus_budget=course.peer_bonus_budget,
            current_evaluation=current_evaluation,
            authored_peer_feedback=authored_peer_feedback,
            results_unlocked=p.results_unlocked,
        )

    async def save_course_evaluation(
        self,
        project_id: int,
        body: CourseEvaluationUpsert,
        user: User,
    ) -> CourseEvaluationFormResponse:
        """Create or update the calling student's course evaluation for *project_id*.

        Draft saves (``body.submitted=False``) create or overwrite the evaluation
        row without triggering the auto-unlock check.  Final submissions
        (``body.submitted=True``) additionally call
        ``_check_and_auto_unlock_project`` so that results are unlocked
        automatically once all lecturers and students have submitted.  The
        peer-feedback rows for this evaluation are fully replaced on every call.

        Raises ``ProjectNotFoundError`` when the project does not exist.
        Raises ``PermissionDeniedError`` when *user* is not a student or not a project member.
        Raises ``EvaluationConflictError`` when the project results are already
        unlocked (editing is no longer permitted after unlock).
        Raises ``InvalidEvaluationDataError`` when ``submitted=True`` but ``rating``
        is ``None``, when peer feedback is provided for a non-team course, a
        recipient ID appears more than once, a recipient is not a project teammate,
        bonus points are non-zero when the course has no peer-bonus scheme, bonus
        points are negative or exceed ``2 × peer_bonus_budget``, or the total bonus
        does not equal ``peer_bonus_budget × N_teammates`` on a final submission.
        """
        row = await db_get_project(self._session, project_id)
        if row is None:
            raise ProjectNotFoundError(project_id)

        p, course = row
        user_id = require_user_id(user)

        if user.role != UserRole.STUDENT:
            raise PermissionDeniedError("Only students may submit a course evaluation.")

        if not await is_project_member(self._session, project_id, user_id):
            raise PermissionDeniedError(f"User {user_id} is not a member of project {project_id}.")

        if p.results_unlocked:
            raise EvaluationConflictError(
                f"Project {project_id} results are already unlocked;"
                " course evaluation cannot be edited."
            )

        # A final submission requires a rating; drafts may omit it.
        if body.submitted and body.rating is None:
            raise InvalidEvaluationDataError(
                "Rating is required when submitting a course evaluation."
            )

        # Peer feedback is only meaningful on team courses; reject it for individual courses.
        if course.project_type != ProjectType.TEAM and body.peer_feedback:
            raise InvalidEvaluationDataError(
                "Peer feedback can only be submitted for team courses."
            )

        # Validate that peer feedback recipients are actual teammates.
        members_by_project = await get_project_members(self._session, [project_id])
        all_members = members_by_project.get(project_id, [])
        teammate_ids = {m.id for m in all_members if m.id is not None and m.id != user_id}

        # Duplicate recipients would cause a DB integrity error; catch them early.
        seen_recipient_ids: set[int] = set()
        for fb in body.peer_feedback:
            if fb.receiving_student_id in seen_recipient_ids:
                raise InvalidEvaluationDataError(
                    f"Duplicate peer feedback recipient id {fb.receiving_student_id}."
                    " Each teammate may appear at most once."
                )
            seen_recipient_ids.add(fb.receiving_student_id)

        invalid_recipients = seen_recipient_ids - teammate_ids
        if invalid_recipients:
            raise InvalidEvaluationDataError(
                f"Invalid peer feedback recipient IDs: {sorted(invalid_recipients)}."
                " Only project teammates may receive peer feedback."
            )

        # Validate bonus points. When the peer-bonus scheme is disabled (budget is None),
        # all bonus_points must be zero to prevent skewing the overview aggregation.
        if course.peer_bonus_budget is None:
            for fb in body.peer_feedback:
                if fb.bonus_points != 0:
                    raise InvalidEvaluationDataError(
                        "Bonus points must be zero when the course has no peer-bonus scheme,"
                        f" got {fb.bonus_points}."
                    )
        else:
            for fb in body.peer_feedback:
                if fb.bonus_points < 0:
                    raise InvalidEvaluationDataError(
                        f"Bonus points must be non-negative, got {fb.bonus_points}."
                    )
                if fb.bonus_points > 2 * course.peer_bonus_budget:
                    raise InvalidEvaluationDataError(
                        f"Bonus points for a single teammate must not exceed"
                        f" 2 × peer_bonus_budget ({2 * course.peer_bonus_budget}),"
                        f" got {fb.bonus_points}."
                    )

            # On a final submission, the total distributed bonus must equal
            # peer_bonus_budget × number_of_teammates (each teammate is worth one budget unit).
            if body.submitted:
                total_bonus = sum(fb.bonus_points for fb in body.peer_feedback)
                expected_total = len(teammate_ids) * course.peer_bonus_budget
                if total_bonus != expected_total:
                    raise InvalidEvaluationDataError(
                        f"Total peer bonus points must equal peer_bonus_budget × teammates"
                        f" ({course.peer_bonus_budget} × {len(teammate_ids)} = {expected_total}),"
                        f" got {total_bonus}."
                    )

        evaluation = await upsert_course_evaluation(
            self._session,
            project_id,
            user_id,
            rating=body.rating,
            strengths=body.strengths,
            improvements=body.improvements,
            submitted=body.submitted,
        )

        if evaluation.id is None:
            raise ValueError(f"CourseEvaluation returned from DB has no id: {evaluation!r}")

        # Peer feedback is only stored for team courses.
        if course.project_type == ProjectType.TEAM:
            feedback_items: list[dict[str, object]] = [
                {
                    "receiving_student_id": fb.receiving_student_id,
                    "strengths": fb.strengths,
                    "improvements": fb.improvements,
                    "bonus_points": fb.bonus_points,
                }
                for fb in body.peer_feedback
            ]
            await replace_peer_feedback(self._session, evaluation.id, feedback_items)
        await self._session.commit()

        if body.submitted:
            await _check_and_auto_unlock_project(self._session, project_id)
            await self._session.commit()

        return await self.get_course_evaluation_form(project_id, user)
