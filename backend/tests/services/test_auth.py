from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from models.user import User, UserRole
from services.auth import (
    is_admin_or_course_lecturer,
    require_course_lecturer_access,
    require_course_manage_access,
)

# ---------------------------------------------------------------------------
# is_admin_or_course_lecturer
# ---------------------------------------------------------------------------


def test_admin_user_always_has_access() -> None:
    """An ADMIN user must be granted access regardless of the lecturer set."""
    user = MagicMock(spec=User)
    user.role = UserRole.ADMIN
    user.id = 1
    assert is_admin_or_course_lecturer(user, set()) is True


def test_assigned_lecturer_has_access() -> None:
    """A LECTURER whose id appears in the lecturer set must be granted access."""
    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 5
    assert is_admin_or_course_lecturer(user, {5, 6}) is True


def test_unassigned_lecturer_denied() -> None:
    """A LECTURER whose id is NOT in the lecturer set must be denied access."""
    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 9
    assert is_admin_or_course_lecturer(user, {5, 6}) is False


def test_student_always_denied() -> None:
    """A STUDENT must always be denied access."""
    user = MagicMock(spec=User)
    user.role = UserRole.STUDENT
    user.id = 1
    assert is_admin_or_course_lecturer(user, {1}) is False


def test_none_user_denied() -> None:
    """An unauthenticated caller (``None``) must always be denied access."""
    assert is_admin_or_course_lecturer(None, {1, 2}) is False


# ---------------------------------------------------------------------------
# require_course_manage_access
# ---------------------------------------------------------------------------


async def test_manage_access_grants_admin_without_db_query() -> None:
    """Admin users must be granted access without querying the DB for lecturers."""
    user = MagicMock(spec=User)
    user.role = UserRole.ADMIN
    user.id = 1

    session = AsyncMock()
    # Should return without calling any DB functions.
    await require_course_manage_access(session, course_id=10, user=user)
    session.execute.assert_not_called()


async def test_manage_access_grants_assigned_lecturer() -> None:
    """A lecturer who is assigned to the course must be granted manage access."""
    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 5

    lecturer_user = MagicMock(spec=User)
    lecturer_user.id = 5

    session = AsyncMock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "services.auth.get_course_lecturers",
            AsyncMock(return_value={10: [lecturer_user]}),
        )
        await require_course_manage_access(session, course_id=10, user=user)


async def test_manage_access_raises_for_unassigned_lecturer() -> None:
    """A lecturer NOT assigned to the course must be denied with ``PermissionError``."""
    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 99

    session = AsyncMock()
    with (
        pytest.MonkeyPatch.context() as mp,
        pytest.raises(PermissionError),
    ):
        mp.setattr(
            "services.auth.get_course_lecturers",
            AsyncMock(return_value={10: []}),
        )
        await require_course_manage_access(session, course_id=10, user=user)


async def test_manage_access_raises_for_student() -> None:
    """A STUDENT must always be denied manage access."""
    user = MagicMock(spec=User)
    user.role = UserRole.STUDENT
    user.id = 1

    session = AsyncMock()
    with (
        pytest.MonkeyPatch.context() as mp,
        pytest.raises(PermissionError),
    ):
        mp.setattr(
            "services.auth.get_course_lecturers",
            AsyncMock(return_value={10: []}),
        )
        await require_course_manage_access(session, course_id=10, user=user)


# ---------------------------------------------------------------------------
# require_course_lecturer_access
# ---------------------------------------------------------------------------


async def test_lecturer_access_grants_assigned_lecturer() -> None:
    """An explicitly assigned lecturer must pass the strict lecturer check."""
    user = MagicMock(spec=User)
    user.role = UserRole.LECTURER
    user.id = 7

    lecturer_user = MagicMock(spec=User)
    lecturer_user.id = 7

    session = AsyncMock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "services.auth.get_course_lecturers",
            AsyncMock(return_value={10: [lecturer_user]}),
        )
        await require_course_lecturer_access(session, course_id=10, user=user)


async def test_lecturer_access_denies_admin_not_assigned() -> None:
    """An ADMIN who is NOT assigned as a course lecturer must be denied."""
    user = MagicMock(spec=User)
    user.role = UserRole.ADMIN
    user.id = 1

    session = AsyncMock()
    with (
        pytest.MonkeyPatch.context() as mp,
        pytest.raises(PermissionError),
    ):
        mp.setattr(
            "services.auth.get_course_lecturers",
            AsyncMock(return_value={10: []}),
        )
        await require_course_lecturer_access(session, course_id=10, user=user)


async def test_lecturer_access_denies_student() -> None:
    """A STUDENT must always be denied the strict lecturer access check."""
    user = MagicMock(spec=User)
    user.role = UserRole.STUDENT
    user.id = 1

    session = AsyncMock()
    with (
        pytest.MonkeyPatch.context() as mp,
        pytest.raises(PermissionError),
    ):
        mp.setattr(
            "services.auth.get_course_lecturers",
            AsyncMock(return_value={10: []}),
        )
        await require_course_lecturer_access(session, course_id=10, user=user)
