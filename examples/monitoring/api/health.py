from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from clients.fake_http_client import enrich_project_info
from db.fake_db import load_projects_from_db
from settings import Settings, get_settings

_start_time = time.monotonic()

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    db_ok = True
    enrich_ok = True

    try:
        await load_projects_from_db(
            settings.projects_data_file, settings.simulated_db_delay_ms, error_rate=0.0
        )
    except Exception:
        db_ok = False

    try:
        await enrich_project_info(
            "health-check", settings.simulated_http_delay_ms, error_rate=0.0
        )
    except Exception:
        enrich_ok = False

    passing = db_ok and enrich_ok
    health_data = {
        "status": "pass" if passing else "fail",
        "version": settings.otel_service_version,
        "service_id": settings.otel_service_name,
        "description": "TUL PSI Students Projects API",
        "checks": {
            "database:connection": "pass" if db_ok else "fail",
            "enrichment:connection": "pass" if enrich_ok else "fail",
            "uptime": f"{time.monotonic() - _start_time:.2f}s",
        },
    }
    return JSONResponse(status_code=200 if passing else 503, content=health_data)
