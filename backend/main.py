from __future__ import annotations

import logging
import os
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger.json import JsonFormatter

from api.auth import router as auth_router
from api.deps import verify_csrf_token
from api.courses import router as courses_router
from api.health import router as health_router
from api.projects import router as projects_router
from api.users import router as users_router
from observability import setup_otel
from settings import get_settings


def _configure_logging() -> None:
    """Configure root logger to emit structured JSON to stdout.

    All log records — including fields injected via the ``extra`` parameter —
    are serialised as JSON objects, one per line.  This format is compatible
    with log aggregation tools (Loki, Azure Monitor, etc.) and makes the
    ``email`` and other context fields visible in every environment.

    The log level is read directly from the ``LOG_LEVEL`` environment variable
    (defaulting to ``INFO``) so that logging is available before the full
    application settings — which require a database URL — are validated.
    """
    handler = logging.StreamHandler(sys.stdout)
    # Include timestamp, level, logger name, and message in every record.
    # Any extra= fields are automatically appended by JsonFormatter.
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    # Keep uvicorn's access/error logs at the same level so they flow through
    # the same JSON handler rather than the default uvicorn plain-text handler.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = [handler]
        logging.getLogger(name).propagate = False


_configure_logging()

settings = get_settings()
app = FastAPI(
    title="Student Projects Catalogue API",
    dependencies=[Depends(verify_csrf_token)],
)

# Setup OpenTelemetry BEFORE including routers to ensure all requests are traced.
setup_otel(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
