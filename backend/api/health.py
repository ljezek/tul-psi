from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version

import httpx
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session

try:
    # Single source of truth: version declared in pyproject.toml.
    _APP_VERSION: str = version("student-projects-catalogue-backend")
except PackageNotFoundError:
    # Fallback for environments where the package is not installed (e.g. bare source checkout).
    _APP_VERSION = "0.0.0"

router = APIRouter(tags=["health"])


class DependencyStatus(BaseModel):
    """Schema for individual dependency health."""

    status: str = Field(description="'ok' if the dependency is reachable.")
    details: str | None = Field(default=None, description="Optional error message or details.")


class HealthResponse(BaseModel):
    """Schema for the health-check response."""

    status: str = Field(description="Overall service health. 'ok' only if all critical components are healthy.")
    version: str = Field(description="Application version string (SemVer).")
    database: DependencyStatus
    otel_collector: DependencyStatus


async def _check_database(session: AsyncSession) -> DependencyStatus:
    """Check database connectivity by executing a simple query."""
    try:
        await session.execute(text("SELECT 1"))
        return DependencyStatus(status="ok")
    except Exception as exc:
        return DependencyStatus(status="error", details=str(exc))


async def _check_otel_collector() -> DependencyStatus:
    """Check OTel collector availability via its health check extension."""
    # The collector runs as a sidecar, so it's always on localhost.
    # The port 13133 is the default for the health_check extension.
    url = "http://localhost:13133"
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return DependencyStatus(status="ok")
            return DependencyStatus(status="error", details=f"HTTP {response.status_code}")
    except Exception as exc:
        return DependencyStatus(status="error", details=str(exc))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Deep health check",
    description=(
        "Returns the current health status of the service and its dependencies. "
        "Performs a database 'ping' and checks the OTel sidecar availability."
    ),
    responses={
        503: {"model": HealthResponse, "description": "Service or a dependency is unhealthy."}
    },
)
async def health(
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> HealthResponse:
    """Return service and dependency status."""
    db_status = await _check_database(session)
    otel_status = await _check_otel_collector()

    overall_status = "ok"
    if db_status.status != "ok" or otel_status.status != "ok":
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        version=_APP_VERSION,
        database=db_status,
        otel_collector=otel_status,
    )
