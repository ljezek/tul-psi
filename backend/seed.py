"""Development seed script for the Student Projects Catalogue.

Populates the local PostgreSQL database with a realistic dataset that covers
the major roles and edge cases described in the product specification:

* 1 admin, 3 lecturers, and all students from data/projects.json plus extra
  synthetic students for past-year courses.
* Two courses: PSI (Projektový seminář informatiky)
  - 2025: fully completed — all projects have lecturer evaluations, course
    evaluations, peer feedback, and results_unlocked=True.
  - 2026: in-progress — projects sourced from data/projects.json; some are
    fully filled in, some are skeleton entries where a student was invited
    but has not yet completed the project details.
* One individual-project course (KDP, 2025) without peer-bonus to exercise
  the individual-type and no-peer-bonus path.

Edge cases exercised
--------------------
* Invited student who has not yet accepted (joined_at is None).
* Project with no description / no technologies / no GitHub URL (stub).
* Team project vs individual project.
* Course with peer_bonus_budget vs without.
* results_unlocked True vs False.
* Partial course evaluation (draft, published=False) vs published.

Usage
-----
    # Run from the backend/ directory with the .env file present:
    python seed.py           # idempotent: skips rows that already exist
    python seed.py --reset   # drops all rows first, then re-seeds
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, create_engine, select

from models import (
    Course,
    CourseEvaluation,
    CourseLecturer,
    CourseTerm,
    OtpToken,
    PeerFeedback,
    Project,
    ProjectEvaluation,
    ProjectMember,
    ProjectType,
    User,
    UserRole,
)
from settings import get_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent / "data"


def _now(offset_days: int = 0) -> datetime:
    """Return a timezone-aware UTC datetime shifted by *offset_days*."""
    return datetime.now(UTC) + timedelta(days=offset_days)


def _get_or_create_user(
    session: Session,
    email: str,
    name: str,
    role: UserRole,
    github_alias: str | None = None,
) -> User:
    """Return the existing user or insert and return a new one."""
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        return existing
    user = User(email=email, name=name, role=role, github_alias=github_alias)
    session.add(user)
    session.flush()
    return user


def _get_or_create_course(session: Session, code: str, **kwargs: object) -> Course:
    """Return the existing course or insert and return a new one."""
    existing = session.exec(select(Course).where(Course.code == code)).first()
    if existing:
        return existing
    course = Course(code=code, **kwargs)  # type: ignore[arg-type]
    session.add(course)
    session.flush()
    return course


def _get_or_create_project(
    session: Session,
    title: str,
    course_id: int,
    academic_year: int,
    **kwargs: object,
) -> Project:
    """Return the existing project or insert and return a new one."""
    existing = session.exec(
        select(Project)
        .where(Project.title == title)
        .where(Project.course_id == course_id)
        .where(Project.academic_year == academic_year)
    ).first()
    if existing:
        return existing
    project = Project(title=title, course_id=course_id, academic_year=academic_year, **kwargs)  # type: ignore[arg-type]
    session.add(project)
    session.flush()
    return project


def _ensure_member(
    session: Session,
    project_id: int,
    user_id: int,
    invited_by: int | None = None,
    joined: bool = True,
) -> ProjectMember:
    """Ensure a ProjectMember row exists for the given (project_id, user_id) pair."""
    existing = session.exec(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .where(ProjectMember.user_id == user_id)
    ).first()
    if existing:
        return existing
    joined_at = _now(-30) if joined else None
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        invited_by=invited_by,
        joined_at=joined_at,
    )
    session.add(member)
    session.flush()
    return member


def _ensure_course_lecturer(session: Session, course_id: int, user_id: int) -> None:
    """Ensure a CourseLecturer association exists."""
    existing = session.exec(
        select(CourseLecturer)
        .where(CourseLecturer.course_id == course_id)
        .where(CourseLecturer.user_id == user_id)
    ).first()
    if existing:
        return
    session.add(CourseLecturer(course_id=course_id, user_id=user_id))
    session.flush()


def _ensure_project_evaluation(
    session: Session,
    project_id: int,
    lecturer_id: int,
    scores: list[dict[str, object]],
) -> None:
    """Ensure a ProjectEvaluation row exists."""
    existing = session.exec(
        select(ProjectEvaluation)
        .where(ProjectEvaluation.project_id == project_id)
        .where(ProjectEvaluation.lecturer_id == lecturer_id)
    ).first()
    if existing:
        return
    evaluation = ProjectEvaluation(
        project_id=project_id,
        lecturer_id=lecturer_id,
        scores=scores,  # type: ignore[arg-type]
        submitted_at=_now(-45),
    )
    session.add(evaluation)
    session.flush()


def _ensure_course_evaluation(
    session: Session,
    project_id: int,
    student_id: int,
    rating: int,
    strengths: str | None,
    improvements: str | None,
    published: bool,
) -> CourseEvaluation:
    """Ensure a CourseEvaluation row exists and return it."""
    existing = session.exec(
        select(CourseEvaluation)
        .where(CourseEvaluation.project_id == project_id)
        .where(CourseEvaluation.student_id == student_id)
    ).first()
    if existing:
        return existing
    evaluation = CourseEvaluation(
        project_id=project_id,
        student_id=student_id,
        rating=rating,
        strengths=strengths,
        improvements=improvements,
        published=published,
        submitted_at=_now(-40),
    )
    session.add(evaluation)
    session.flush()
    return evaluation


def _ensure_peer_feedback(
    session: Session,
    course_evaluation_id: int,
    receiving_student_id: int,
    strengths: str | None,
    improvements: str | None,
    bonus_points: int,
) -> None:
    """Ensure a PeerFeedback row exists."""
    existing = session.exec(
        select(PeerFeedback)
        .where(PeerFeedback.course_evaluation_id == course_evaluation_id)
        .where(PeerFeedback.receiving_student_id == receiving_student_id)
    ).first()
    if existing:
        return
    session.add(
        PeerFeedback(
            course_evaluation_id=course_evaluation_id,
            receiving_student_id=receiving_student_id,
            strengths=strengths,
            improvements=improvements,
            bonus_points=bonus_points,
        )
    )
    session.flush()


# ---------------------------------------------------------------------------
# Reset helper
# ---------------------------------------------------------------------------


def _reset_database(session: Session) -> None:
    """Delete all rows from application tables in FK-safe order."""
    print("Resetting database …")
    # Deletion order respects FK dependencies: children before parents.
    for model in (
        PeerFeedback,
        CourseEvaluation,
        ProjectEvaluation,
        ProjectMember,
        CourseLecturer,
        Project,
        OtpToken,
        Course,
        User,
    ):
        session.exec(delete(model))  # type: ignore[call-overload]
    session.commit()
    print("Reset complete.")


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

_PSI_CRITERIA_2025 = [
    {
        "code": "architecture",
        "description": "Architektura a návrh systému",
        "max_score": 20,
    },
    {
        "code": "code_quality",
        "description": "Kvalita kódu a dodržení konvencí",
        "max_score": 20,
    },
    {
        "code": "testing",
        "description": "Testování a pokrytí kódu",
        "max_score": 20,
    },
    {
        "code": "documentation",
        "description": "Dokumentace a README",
        "max_score": 20,
    },
    {
        "code": "presentation",
        "description": "Prezentace a demo",
        "max_score": 20,
    },
]

_PSI_CRITERIA_2026 = [
    {
        "code": "architecture",
        "description": "Architektura a návrh systému",
        "max_score": 25,
    },
    {
        "code": "code_quality",
        "description": "Kvalita kódu a dodržení konvencí",
        "max_score": 25,
    },
    {
        "code": "testing",
        "description": "Testování a pokrytí kódu",
        "max_score": 25,
    },
    {
        "code": "presentation",
        "description": "Prezentace a demo",
        "max_score": 25,
    },
]

_KDP_CRITERIA = [
    {
        "code": "analysis",
        "description": "Analýza a specifikace požadavků",
        "max_score": 30,
    },
    {
        "code": "implementation",
        "description": "Implementace a funkčnost",
        "max_score": 40,
    },
    {
        "code": "report",
        "description": "Technická zpráva",
        "max_score": 30,
    },
]

_PSI_LINKS = [
    {"label": "Moodle", "url": "https://moodle.tul.cz/course/view.php?id=12345"},
    {"label": "GitHub Organisation", "url": "https://github.com/PSI-RDB-2026"},
]

# ---------------------------------------------------------------------------
# Past-year (2025) synthetic students and projects
# ---------------------------------------------------------------------------

_PAST_STUDENTS: list[dict[str, str]] = [
    {"name": "Alice Nováková", "email": "alice.novakova@tul.cz", "github": "alicenov"},
    {"name": "Bob Krček", "email": "bob.krcek@tul.cz", "github": "bobkrcek"},
    {"name": "Carol Blažková", "email": "carol.blazkova@tul.cz", "github": "carolblaz"},
    {"name": "Dan Horák", "email": "dan.horak@tul.cz", "github": "danhorak"},
    {"name": "Eva Marková", "email": "eva.markova@tul.cz", "github": "evamark"},
    {"name": "Filip Žák", "email": "filip.zak@tul.cz", "github": "filipzak"},
]

# Three synthetic past-year projects.  Each maps title → list of student indices.
_PAST_PROJECTS: list[dict[str, object]] = [
    {
        "title": "TUL Event Planner",
        "description": "Webová aplikace pro správu a přihlašování na fakultní akce a workshopy.",
        "github_url": "https://github.com/PSI-2025/event-planner",
        "live_url": "https://event-planner.tul.cz",
        "technologies": ["Python", "FastAPI", "React", "PostgreSQL"],
        "members": [0, 1],  # indices into _PAST_STUDENTS
    },
    {
        "title": "Studijní Asistent",
        "description": (
            "Chatbot integrovaný s Moodle pro zodpovídání dotazů ke studijním materiálům."
        ),
        "github_url": "https://github.com/PSI-2025/studijni-asistent",
        "live_url": None,
        "technologies": ["Python", "LangChain", "Vue.js"],
        "members": [2, 3, 4],
    },
    {
        "title": "Budget Tracker",
        "description": "Mobilní aplikace pro sledování osobních výdajů s exportem do CSV.",
        "github_url": "https://github.com/PSI-2025/budget-tracker",
        "live_url": "https://budget.tul.cz",
        "technologies": ["Flutter", "Dart", "Firebase"],
        "members": [5, 1],
    },
]

# KDP 2025 — individual projects, no peer bonus.
_KDP_PROJECTS: list[dict[str, object]] = [
    {
        "title": "Analýza výkonnosti distribuovaných systémů",
        "description": "Srovnání latence a propustnosti různých message-broker architektur.",
        "github_url": "https://github.com/alicenov/kdp-2025",
        "technologies": ["Python", "RabbitMQ", "Kafka"],
        "student_idx": 0,  # Alice
    },
    {
        "title": "Detekce anomálií v IoT datech pomocí ML",
        "description": "Klasifikace chybových stavů senzorů pomocí izolačního lesa.",
        "github_url": "https://github.com/danhorak/kdp-2025",
        "technologies": ["Python", "scikit-learn", "MQTT"],
        "student_idx": 3,  # Dan
    },
]


def _scores_for(criteria: list[dict[str, object]], base: int) -> list[dict[str, object]]:
    """Build a list of EvaluationScore dicts from *criteria*, using *base* as the score."""
    result = []
    for crit in criteria:
        max_s = int(crit["max_score"])  # type: ignore[arg-type]
        score = min(base, max_s)
        result.append(
            {
                "criterion_code": crit["code"],
                "score": score,
                "strengths": f"Výborná práce v oblasti {crit['description']}.",
                "improvements": (
                    f"Doporučuji věnovat více pozornosti detailům v {crit['description']}."
                ),
            }
        )
    return result


# ---------------------------------------------------------------------------
# Main seed routine
# ---------------------------------------------------------------------------


def seed(session: Session) -> None:  # noqa: C901 — long but linear seeding logic
    """Insert all seed rows into the database via *session*."""

    # ------------------------------------------------------------------ users
    print("Seeding users …")

    admin = _get_or_create_user(
        session,
        email="psi.admin@tul.cz",
        name="PSI Admin",
        role=UserRole.ADMIN,
        github_alias="psi-admin",
    )

    lecturer_novak = _get_or_create_user(
        session,
        email="jan.novak@tul.cz",
        name="Jan Novák",
        role=UserRole.LECTURER,
        github_alias="jannovak",
    )
    lecturer_svoboda = _get_or_create_user(
        session,
        email="petra.svoboda@tul.cz",
        name="Petra Svobodová",
        role=UserRole.LECTURER,
        github_alias="petrasvo",
    )
    lecturer_kral = _get_or_create_user(
        session,
        email="tomas.kral@tul.cz",
        name="Tomáš Král",
        role=UserRole.LECTURER,
        github_alias="tomaskral",
    )

    # Load 2026 students from data/projects.json.
    projects_json_path = _DATA_DIR / "projects.json"
    with projects_json_path.open(encoding="utf-8") as fh:
        catalogue: dict[str, list[dict[str, object]]] = json.load(fh)
    json_projects_2026 = catalogue.get("2026", [])

    # Collect all unique students from the JSON data.
    seen_emails: set[str] = set()
    current_students: list[User] = []
    for proj_data in json_projects_2026:
        members = proj_data.get("members", [])
        for member in members:  # type: ignore[union-attr]
            email = str(member["tul_email"])  # type: ignore[index]
            if email in seen_emails:
                continue
            seen_emails.add(email)
            user = _get_or_create_user(
                session,
                email=email,
                name=str(member["name"]),  # type: ignore[index]
                role=UserRole.STUDENT,
                github_alias=(
                    str(member.get("github_alias")) if member.get("github_alias") else None
                ),  # type: ignore[arg-type]
            )
            current_students.append(user)

    # Create synthetic past-year students (used in 2025 courses).
    past_student_users: list[User] = []
    for s in _PAST_STUDENTS:
        user = _get_or_create_user(
            session,
            email=s["email"],
            name=s["name"],
            role=UserRole.STUDENT,
            github_alias=s["github"],
        )
        past_student_users.append(user)

    # ---------------------------------------------------------------- courses
    print("Seeding courses …")

    # PSI 2025 — completed course with all evaluations finalized.
    course_psi_2025 = _get_or_create_course(
        session,
        code="PSI-2025",
        name="Projektový seminář informatiky",
        syllabus=(
            "Studenti v týmech navrhnou a implementují netriviální softwarový projekt. "
            "Důraz je kladen na architekturu, testování a dokumentaci."
        ),
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=50,
        peer_bonus_budget=10,
        evaluation_criteria=_PSI_CRITERIA_2025,
        links=_PSI_LINKS,
        created_by=admin.id,
    )

    # PSI 2026 — current course, projects in progress.
    course_psi_2026 = _get_or_create_course(
        session,
        code="PSI-2026",
        name="Projektový seminář informatiky",
        syllabus=(
            "Studenti v týmech navrhnou a implementují netriviální softwarový projekt. "
            "Hodnocení zahrnuje architekturu, kvalitu kódu, testování a prezentaci."
        ),
        term=CourseTerm.WINTER,
        project_type=ProjectType.TEAM,
        min_score=60,
        peer_bonus_budget=10,
        evaluation_criteria=_PSI_CRITERIA_2026,
        links=_PSI_LINKS,
        created_by=admin.id,
    )

    # KDP 2025 — individual project course, no peer bonus.
    course_kdp_2025 = _get_or_create_course(
        session,
        code="KDP-2025",
        name="Klauzurní projekt",
        syllabus=(
            "Individuální softwarový nebo výzkumný projekt obhajovaný u státní závěrečné zkoušky."
        ),
        term=CourseTerm.SUMMER,
        project_type=ProjectType.INDIVIDUAL,
        min_score=60,
        peer_bonus_budget=None,  # No peer bonus for individual projects.
        evaluation_criteria=_KDP_CRITERIA,
        links=[],
        created_by=admin.id,
    )

    # --------------------------------------------------- course–lecturer links
    print("Seeding course–lecturer assignments …")
    _ensure_course_lecturer(session, course_psi_2025.id, lecturer_novak.id)  # type: ignore[arg-type]
    _ensure_course_lecturer(session, course_psi_2025.id, lecturer_svoboda.id)  # type: ignore[arg-type]
    _ensure_course_lecturer(session, course_psi_2026.id, lecturer_novak.id)  # type: ignore[arg-type]
    _ensure_course_lecturer(session, course_psi_2026.id, lecturer_kral.id)  # type: ignore[arg-type]
    _ensure_course_lecturer(session, course_kdp_2025.id, lecturer_svoboda.id)  # type: ignore[arg-type]

    # ---------------------------------------- PSI 2025 — completed projects
    print("Seeding PSI 2025 projects (completed) …")

    past_project_records: list[Project] = []
    for proj_data in _PAST_PROJECTS:
        p = _get_or_create_project(
            session,
            title=str(proj_data["title"]),
            course_id=course_psi_2025.id,  # type: ignore[arg-type]
            academic_year=2025,
            description=proj_data.get("description"),
            github_url=proj_data.get("github_url"),
            live_url=proj_data.get("live_url"),
            technologies=proj_data.get("technologies", []),
            results_unlocked=True,
        )
        past_project_records.append(p)

        # Add project members (all joined for completed projects).
        member_indices: list[int] = proj_data.get("members", [])  # type: ignore[assignment]
        for i, idx in enumerate(member_indices):
            invited_by = past_student_users[member_indices[0]].id if i > 0 else None
            _ensure_member(
                session,
                project_id=p.id,  # type: ignore[arg-type]
                user_id=past_student_users[idx].id,  # type: ignore[arg-type]
                invited_by=invited_by,
                joined=True,
            )

        # Lecturer evaluation — both lecturers evaluate all 2025 projects.
        _ensure_project_evaluation(
            session,
            project_id=p.id,  # type: ignore[arg-type]
            lecturer_id=lecturer_novak.id,  # type: ignore[arg-type]
            scores=_scores_for(_PSI_CRITERIA_2025, 16),
        )
        _ensure_project_evaluation(
            session,
            project_id=p.id,  # type: ignore[arg-type]
            lecturer_id=lecturer_svoboda.id,  # type: ignore[arg-type]
            scores=_scores_for(_PSI_CRITERIA_2025, 18),
        )

        # Course evaluations + peer feedback for every team member.
        member_ids = [past_student_users[idx].id for idx in member_indices]  # type: ignore[index]
        for student_id in member_ids:
            # Alternate between published and draft to test both states.
            # The first student submits a published evaluation; others also published
            # for the completed-course scenario (all feedback in).
            ce = _ensure_course_evaluation(
                session,
                project_id=p.id,  # type: ignore[arg-type]
                student_id=student_id,  # type: ignore[arg-type]
                rating=4,
                strengths="Kurz byl výborně organizován a přednášky byly srozumitelné.",
                improvements="Uvítal bych více praktických cvičení v první polovině semestru.",
                published=True,
            )

            # Peer feedback for every *other* member.
            other_ids = [uid for uid in member_ids if uid != student_id]
            total_budget = 10  # peer_bonus_budget for this course
            per_person_bonus = total_budget // len(other_ids) if other_ids else 0
            for receiving_id in other_ids:
                _ensure_peer_feedback(
                    session,
                    course_evaluation_id=ce.id,  # type: ignore[arg-type]
                    receiving_student_id=receiving_id,  # type: ignore[arg-type]
                    strengths="Spolehlivý člen týmu, vždy včas plnil zadané úkoly.",
                    improvements="Doporučuji aktivnější komunikaci při blokujících problémech.",
                    bonus_points=per_person_bonus,
                )

    # ---------------------------------------- PSI 2026 — current projects
    print("Seeding PSI 2026 projects (from data/projects.json) …")

    # Build a lookup: email → User for quick member resolution.
    all_users_by_email: dict[str, User] = {}
    for user in session.exec(select(User)).all():
        all_users_by_email[user.email] = user

    for proj_index, proj_data in enumerate(json_projects_2026):
        members_raw: list[dict[str, str]] = proj_data.get("members", [])  # type: ignore[assignment]
        if not members_raw:
            continue

        # Decide on the completeness state based on project index to exercise
        # different edge cases:
        #   0 — fully filled in (description, GitHub, technologies set)
        #   1 — partially filled (GitHub set, no description or technologies)
        #   2 — stub (only title seeded; first student invited but not yet joined)
        #   3+ — normal in-progress (description and GitHub, no live_url)
        is_complete = proj_index == 0
        is_partial = proj_index == 1
        is_stub = proj_index == 2

        github_url = str(proj_data.get("github_repo_url", "")) or None

        if is_complete:
            description = (
                "Plná implementace Student Projects Catalogue —"
                " React SPA + FastAPI backend + PostgreSQL."
            )
            technologies = ["React", "TypeScript", "FastAPI", "Python", "PostgreSQL", "Docker"]
            live_url: str | None = "https://psi.tul.cz"
        elif is_partial:
            description = None  # Student hasn't filled in description yet.
            technologies = []
            live_url = None
        elif is_stub:
            description = None
            technologies = []
            live_url = None
            github_url = None  # Project owner hasn't even linked a repo.
        else:
            description = f"Webová aplikace: {proj_data['project_name']}."
            technologies = ["Python", "React"]
            live_url = None

        project = _get_or_create_project(
            session,
            title=str(proj_data["project_name"]),
            course_id=course_psi_2026.id,  # type: ignore[arg-type]
            academic_year=2026,
            description=description,
            github_url=github_url,
            live_url=live_url,
            technologies=technologies,
            results_unlocked=False,
        )

        owner_email = str(members_raw[0]["tul_email"])
        owner_user = all_users_by_email.get(owner_email)
        if owner_user is None:
            continue  # Should never happen — users were created above.

        # Owner is always a direct member (no invite chain).
        _ensure_member(session, project_id=project.id, user_id=owner_user.id, joined=True)  # type: ignore[arg-type]

        for i, member_raw in enumerate(members_raw[1:], start=1):
            member_email = str(member_raw["tul_email"])
            member_user = all_users_by_email.get(member_email)
            if member_user is None:
                continue

            # For the stub project: second member was invited but hasn't joined.
            # For all others: all members have joined.
            joined = not (is_stub and i == 1)
            _ensure_member(
                session,
                project_id=project.id,  # type: ignore[arg-type]
                user_id=member_user.id,  # type: ignore[arg-type]
                invited_by=owner_user.id,
                joined=joined,
            )

    # ------------------------------------ KDP 2025 — individual completed projects
    print("Seeding KDP 2025 projects (individual, completed) …")

    for kdp_data in _KDP_PROJECTS:
        student = past_student_users[int(kdp_data["student_idx"])]  # type: ignore[arg-type]
        p = _get_or_create_project(
            session,
            title=str(kdp_data["title"]),
            course_id=course_kdp_2025.id,  # type: ignore[arg-type]
            academic_year=2025,
            description=kdp_data.get("description"),
            github_url=kdp_data.get("github_url"),
            technologies=kdp_data.get("technologies", []),
            results_unlocked=True,
        )
        _ensure_member(session, project_id=p.id, user_id=student.id, joined=True)  # type: ignore[arg-type]

        _ensure_project_evaluation(
            session,
            project_id=p.id,  # type: ignore[arg-type]
            lecturer_id=lecturer_svoboda.id,  # type: ignore[arg-type]
            scores=_scores_for(_KDP_CRITERIA, 25),
        )

        # Individual course — no peer bonus — published course evaluation.
        _ensure_course_evaluation(
            session,
            project_id=p.id,  # type: ignore[arg-type]
            student_id=student.id,  # type: ignore[arg-type]
            rating=5,
            strengths="Práce na projektu mi dala skvělou přípravu na obhajobu.",
            improvements="Více konzultačních termínů by pomohlo v průběhu zpracování.",
            published=True,
        )
        # No PeerFeedback rows — peer_bonus_budget is None for KDP.

    # ---------------------------------------------- draft evaluation edge-case
    # One 2026 student has started a draft course evaluation (published=False)
    # to exercise the partial-submission code path.
    print("Seeding draft course evaluation edge-case …")

    if json_projects_2026:
        first_project_2026 = session.exec(
            select(Project)
            .where(Project.course_id == course_psi_2026.id)
            .where(Project.academic_year == 2026)
        ).first()
        if first_project_2026:
            first_member_raw = json_projects_2026[0].get("members", [{}])[0]  # type: ignore[index]
            draft_student_email = str(first_member_raw.get("tul_email", ""))
            draft_student = all_users_by_email.get(draft_student_email)
            if draft_student:
                _ensure_course_evaluation(
                    session,
                    project_id=first_project_2026.id,  # type: ignore[arg-type]
                    student_id=draft_student.id,  # type: ignore[arg-type]
                    rating=4,
                    strengths=None,  # Draft — free-text not filled in yet.
                    improvements=None,
                    published=False,
                )

    session.commit()
    print("Seed complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments and run the seed routine."""
    parser = argparse.ArgumentParser(description="Seed the development database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing rows before seeding (full re-seed).",
    )
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        if args.reset:
            _reset_database(session)
        seed(session)

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
