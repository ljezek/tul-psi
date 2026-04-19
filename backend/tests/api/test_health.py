from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from db.session import get_session
from main import app


@pytest.fixture(autouse=True)
def _mock_dependencies() -> Generator[None, None, None]:
    """Mock database dependency for health check tests."""
    mock_session = AsyncMock()
    # Default to healthy database
    mock_session.execute.return_value = AsyncMock()

    app.dependency_overrides[get_session] = lambda: mock_session
    yield
    app.dependency_overrides.pop(get_session, None)


async def test_health_returns_200_when_healthy(client: AsyncClient, respx_mock) -> None:
    """GET /health must respond with HTTP 200 and 'pass' status when all services are up."""
    # Mock OTel collector health check
    respx_mock.get("http://localhost:13133").respond(status_code=200)

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/health+json"

    data = response.json()
    assert data["status"] == "pass"
    assert data["checks"]["postgresql:connection"][0]["status"] == "pass"
    assert data["checks"]["otel:collector"][0]["status"] == "pass"


async def test_health_returns_503_when_db_down(client: AsyncClient, respx_mock) -> None:
    """GET /health must respond with HTTP 503 and 'fail' status when database is down."""
    # Simulate DB failure
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("DB Connection Error")
    app.dependency_overrides[get_session] = lambda: mock_session

    # Mock OTel collector as healthy
    respx_mock.get("http://localhost:13133").respond(status_code=200)

    response = await client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "fail"
    assert data["checks"]["postgresql:connection"][0]["status"] == "fail"
    assert "DB Connection Error" in data["checks"]["postgresql:connection"][0]["output"]


async def test_health_returns_200_with_warn_when_otel_down(client: AsyncClient, respx_mock) -> None:
    """GET /health must respond with HTTP 200 and 'warn' status
    when OTel is down (optional dependency)."""
    # Mock OTel collector failure
    respx_mock.get("http://localhost:13133").respond(status_code=500)

    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "warn"
    assert data["checks"]["postgresql:connection"][0]["status"] == "pass"
    assert data["checks"]["otel:collector"][0]["status"] == "warn"


async def test_health_contains_version_and_release_id(client: AsyncClient, respx_mock) -> None:
    """GET /health response must contain version and releaseId."""
    respx_mock.get("http://localhost:13133").respond(status_code=200)

    response = await client.get("/health")
    data = response.json()

    assert "version" in data
    assert "releaseId" in data
    assert data["version"] == data["releaseId"]
