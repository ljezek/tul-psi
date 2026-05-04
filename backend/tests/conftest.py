from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Provide a syntactically valid DATABASE_URL so that pydantic-settings can
# instantiate Settings when main.py is imported.  The URL is never used in
# unit tests because all database sessions are replaced by AsyncMock fixtures.
# This must be set before "from main import app" triggers get_settings().
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
# Disable IP-based rate limiting in unit tests so that tests sending many
# requests to the same endpoint are not blocked by in-memory counters.
os.environ.setdefault("DISABLE_RATE_LIMIT", "true")

from main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
