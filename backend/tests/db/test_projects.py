from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# DB layer unit tests
# ---------------------------------------------------------------------------


async def test_get_project_members_returns_empty_dict_for_empty_ids() -> None:
    """``get_project_members`` must short-circuit and return ``{}`` for an empty id list."""
    from db.projects import get_project_members

    session = AsyncMock()
    result = await get_project_members(session, [])
    assert result == {}
    session.execute.assert_not_called()


async def test_get_course_lecturers_returns_empty_dict_for_empty_ids() -> None:
    """``get_course_lecturers`` must short-circuit and return ``{}`` for an empty id list."""
    from db.projects import get_course_lecturers

    session = AsyncMock()
    result = await get_course_lecturers(session, [])
    assert result == {}
    session.execute.assert_not_called()


def test_escape_like_escapes_wildcards() -> None:
    """``_escape_like`` must escape ``%``, ``_``, and backslash characters."""
    from db.projects import _escape_like

    assert _escape_like("100%") == "100\\%"
    assert _escape_like("user_name") == "user\\_name"
    assert _escape_like("back\\slash") == "back\\\\slash"


async def test_db_get_project_returns_none_when_not_found() -> None:
    """``get_project`` must return ``None`` when the session yields no matching row."""
    from db.projects import get_project as db_get_project

    mock_result = MagicMock()
    mock_result.first.return_value = None
    session = AsyncMock()
    session.execute.return_value = mock_result

    result = await db_get_project(session, 999)

    assert result is None


async def test_db_get_project_returns_project_course_tuple_when_found() -> None:
    """``get_project`` must return a ``(Project, Course)`` tuple when a matching row exists."""
    from db.projects import get_project as db_get_project
    from models.course import Course
    from models.project import Project

    project = MagicMock(spec=Project)
    course = MagicMock(spec=Course)

    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, i: (project, course)[i]
    mock_result = MagicMock()
    mock_result.first.return_value = mock_row
    session = AsyncMock()
    session.execute.return_value = mock_result

    result = await db_get_project(session, 1)

    assert result is not None
    assert result == (project, course)
