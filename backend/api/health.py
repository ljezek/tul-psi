from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version

import httpx
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session

logger = logging.getLogger(__name__)

try:
    _APP_VERSION: str = version("student-projects-catalogue-backend")
except PackageNotFoundError:
    _APP_VERSION = "0.0.0"

router = APIRouter(tags=["health"])

class ComponentCheck(BaseModel):
    """Schema for RFC-compliant component check details."""
    status: str = Field(description="Indicates whether the component is healthy. 'pass', 'warn', or 'fail'.")
    componentId: str | None = Field(default=None, description="Unique identifier for the component.")
    componentType: str | None = Field(default=None, description="The type of the component.")
    observedValue: str | None = Field(default=None, description="The observed value of the check.")
    output: str | None = Field(default=None, description="The output of the check (e.g. error message).")

class HealthResponse(BaseModel):
    """Schema for RFC-compliant health-check response (application/health+json)."""
    status: str = Field(description="The overall status of the service. 'pass', 'warn', or 'fail'.")
    version: str = Field(description="The version of the service.")
    releaseId: str = Field(description="The release identifier of the service.")
    checks: dict[str, list[ComponentCheck]] = Field(description="Detailed checks for dependencies.")

async def _check_database(session: AsyncSession) -> ComponentCheck:
    """Check critical database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
        return ComponentCheck(status="pass", componentType="datastore")
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return ComponentCheck(status="fail", componentType="datastore", output=str(exc))

async def _check_otel_collector() -> ComponentCheck:
    """Check optional OTel collector availability."""
    url = "http://localhost:13133"
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return ComponentCheck(status="pass", componentType="sidecar")
            return ComponentCheck(status="warn", componentType="sidecar", output=f"HTTP {response.status_code}")
    except Exception as exc:
        # We only warn for OTel as it's an optional dependency
        return ComponentCheck(status="warn", componentType="sidecar", output=str(exc))

@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        200: {"content": {"application/health+json": {}}},
        503: {"content": {"application/health+json": {}}},
    },
    summary="Standard health check",
    description="Returns RFC-compliant health status. DB failure triggers 503; OTel failure only triggers a warning.",
)
async def health(
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> HealthResponse:
    """Perform health checks and return standardized response."""
    response.headers["Content-Type"] = "application/health+json"
    
    db_check = await _check_database(session)
    otel_check = await _check_otel_collector()

    # Database is CRITICAL: fail if it's down
    # OTel is OPTIONAL: warn if it's down, but keep overall status as 'pass' (or 'warn')
    overall_status = "pass"
    if db_check.status == "fail":
        overall_status = "fail"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif otel_check.status == "warn":
        overall_status = "warn"

    return HealthResponse(
        status=overall_status,
        version=_APP_VERSION,
        releaseId=_APP_VERSION,
        checks={
            "postgresql:connection": [db_check],
            "otel:collector": [otel_check],
        },
    )
