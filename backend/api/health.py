from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends

from clients.fake_http_client import enrich_project_info
from db.fake_db import load_projects_from_db
from settings import Settings, get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    data_file = Path(settings.projects_data_file)
    if not data_file.exists():
        return {"status": "not_ready", "reason": "projects_data_file_missing"}

    await load_projects_from_db(settings.projects_data_file, settings.simulated_db_delay_ms)
    await enrich_project_info("readiness-check", settings.simulated_http_delay_ms)
    return {"status": "ready"}
