from __future__ import annotations

from fastapi import FastAPI

from api.health import router as health_router

app = FastAPI(title="Student Projects Catalogue API")

app.include_router(health_router)
