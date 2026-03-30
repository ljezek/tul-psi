from __future__ import annotations

from httpx import AsyncClient


async def test_app_starts(client: AsyncClient) -> None:
    """Verify that the FastAPI application boots without errors."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Student Projects Catalogue API"
