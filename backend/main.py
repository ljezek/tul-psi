from __future__ import annotations

from fastapi import FastAPI

from api.health import router as health_router
from api.projects import router as projects_router

app = FastAPI(title="Student Projects Catalogue API")

app.include_router(health_router)
app.include_router(projects_router, prefix="/api/v1")
