from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter
from pydantic import BaseModel, Field

try:
    # Single source of truth: version declared in pyproject.toml.
    _APP_VERSION: str = version("student-projects-catalogue-backend")
except PackageNotFoundError:
    # Fallback for environments where the package is not installed (e.g. bare source checkout).
    _APP_VERSION = "0.0.0"

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
async def health() -> HealthResponse:
    """Return service liveness status.

    This endpoint is intended as a liveness probe for Azure App Service (and
    similar platforms). It returns HTTP 200 as long as the API process is
    running and able to load its configuration.

    It does not perform deep readiness or dependency checks (for example,
    database connectivity or external service availability). If you require
    a stricter readiness signal, expose a separate readiness endpoint with
    the appropriate checks.
    """
    return HealthResponse(status="ok", version=_APP_VERSION)
