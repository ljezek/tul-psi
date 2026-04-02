from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.courses import get_course_lecturers
from models.user import User, UserRole


def is_admin_or_course_lecturer(
    user: User | None,
    course_lecturer_ids: set[int],
) -> bool:
    """Return ``True`` when *user* is an admin or is assigned as a lecturer for a course.

    Access is granted to:
    - Admin users (any course).
    - Lecturers whose id appears in *course_lecturer_ids*.

    Returns ``False`` for unauthenticated callers (``None``), students, and
    lecturers who are not assigned to the course.
    """
    if user is None:
        return False
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.LECTURER and user.id in course_lecturer_ids:
        return True
    return False


async def require_course_manage_access(
    session: AsyncSession,
    course_id: int,
    user: User,
) -> None:
    """Assert *user* may create, update, or delete resources for *course_id*.

    Admins are granted access unconditionally without a DB query.  For all
    other roles the course-lecturer assignment table is queried; the user id
    must appear there.

    Raises ``PermissionError`` when the user is not authorised.
    """
    if user.role == UserRole.ADMIN:
        return
    lecturers_by_course = await get_course_lecturers(session, [course_id])
    lecturer_users = lecturers_by_course.get(course_id, [])
    lecturer_ids = {u.id for u in lecturer_users if u.id is not None}
    if not is_admin_or_course_lecturer(user, lecturer_ids):
        raise PermissionError(
            f"User {user.id} is not authorised to manage resources for course {course_id}."
        )


async def require_course_lecturer_access(
    session: AsyncSession,
    course_id: int,
    user: User,
) -> None:
    """Assert *user* is explicitly assigned as a lecturer for *course_id*.

    Unlike :func:`require_course_manage_access`, this check does **not** grant
    unconditional access to admins.  An admin user must also appear in the
    course-lecturer assignment table to pass this check.  This stricter gate is
    used for actions that are semantically tied to a lecturer role on the course
    (e.g. submitting a project evaluation), where an unassigned admin should not
    be able to act on behalf of a lecturer.

    Raises ``PermissionError`` when the user's id is not in the assigned-lecturer
    list, regardless of role.
    """
    lecturers_by_course = await get_course_lecturers(session, [course_id])
    lecturer_users = lecturers_by_course.get(course_id, [])
    lecturer_ids = {u.id for u in lecturer_users if u.id is not None}
    if user.id not in lecturer_ids:
        raise PermissionError(
            f"User {user.id} is not assigned as a lecturer for course {course_id}."
        )
