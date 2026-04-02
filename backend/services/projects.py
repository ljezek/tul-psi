from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db.projects import (
    get_course_evaluations,
    get_course_lecturers,
    get_peer_feedback_authored,
    get_peer_feedback_received,
    get_project_evaluations,
    get_project_members,
    get_projects,
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
    CourseEvaluationDetail,
    CoursePublic,
    EvaluationScoreDetail,
    LecturerPublic,
    MemberPublic,
    PeerFeedbackDetail,
    ProjectEvaluationDetail,
    ProjectPublic,
)


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
