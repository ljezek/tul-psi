from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from settings import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Schema for the health-check response."""

    status: str = Field(description="Service health status. 'ok' while the process is healthy.")
    version: str = Field(description="Application version string (SemVer).")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness / readiness check",
    description=(
        "Returns the current health status of the service. "
        "Intended for use as an Azure App Service health probe — "
        "always returns HTTP 200 while the process is running."
    ),
)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return service health status.

    Azure App Service (and similar platforms) poll this endpoint to decide
    whether the instance is healthy.  Returning a non-2xx status causes the
    platform to remove the instance from rotation, so we only return 200 when
    the application is genuinely ready to serve traffic.
    """
    return HealthResponse(status="ok", version=settings.app_version)
