from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from db.courses import get_pending_lecturer_evaluations_count


@pytest.mark.asyncio
async def test_get_pending_evaluations_returns_empty_dict_for_no_courses() -> None:
    """get_pending_lecturer_evaluations_count must return an empty dict when no course_ids are provided."""
    session = AsyncMock()
    result = await get_pending_lecturer_evaluations_count(session, [], 1)
    assert result == {}
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_get_pending_evaluations_returns_zeros_when_no_projects_found() -> None:
    """get_pending_lecturer_evaluations_count must return 0 for all courses when no matching projects exist."""
    mock_result = MagicMock()
    mock_result.all.return_value = []
    session = AsyncMock()
    session.execute.return_value = mock_result

    result = await get_pending_lecturer_evaluations_count(session, [10, 20], 1)

    assert result == {10: 0, 20: 0}


@pytest.mark.asyncio
async def test_get_pending_evaluations_counts_projects_correctly() -> None:
    """get_pending_lecturer_evaluations_count must correctly count pending projects per course."""
    # Mock projects query result: (course_id, count)
    mock_result = MagicMock()
    mock_result.all.return_value = [
        (10, 2),
        (20, 1),
    ]
    session = AsyncMock()
    session.execute.return_value = mock_result

    # Note: We are testing the single-query version now, which returns (course_id, count) rows.
    result = await get_pending_lecturer_evaluations_count(session, [10, 20, 30], 1)

    assert result == {10: 2, 20: 1, 30: 0}
    session.execute.assert_called_once()
