from __future__ import annotations

from fastapi import FastAPI

from api.auth import router as auth_router
from api.health import router as health_router

app = FastAPI(title="Student Projects Catalogue API")

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
