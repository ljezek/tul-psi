from __future__ import annotations

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
