from __future__ import annotations

from httpx import AsyncClient


async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /health must respond with HTTP 200."""
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_returns_status_ok(client: AsyncClient) -> None:
    """GET /health body must contain status='ok'."""
    response = await client.get("/health")
    assert response.json()["status"] == "ok"


async def test_health_returns_version(client: AsyncClient) -> None:
    """GET /health body must contain a non-empty version string."""
    response = await client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"]  # non-empty


async def test_health_response_schema(client: AsyncClient) -> None:
    """GET /health response must have exactly the keys 'status' and 'version'."""
    response = await client.get("/health")
    keys = set(response.json().keys())
    assert keys == {"status", "version"}
