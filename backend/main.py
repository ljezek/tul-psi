from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from pythonjsonlogger.jsonlogger import JsonFormatter

from api.auth import router as auth_router
from api.health import router as health_router
from settings import get_settings


def _configure_logging() -> None:
    """Configure root logger to emit structured JSON to stdout.

    All log records — including fields injected via the ``extra`` parameter —
    are serialised as JSON objects, one per line.  This format is compatible
    with log aggregation tools (Loki, Azure Monitor, etc.) and makes the
    ``email`` and other context fields visible in every environment.
    """
    handler = logging.StreamHandler(sys.stdout)
    # Include timestamp, level, logger name, and message in every record.
    # Any extra= fields are automatically appended by JsonFormatter.
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(get_settings().log_level.upper())

    # Keep uvicorn's access/error logs at the same level so they flow through
    # the same JSON handler rather than the default uvicorn plain-text handler.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = [handler]
        logging.getLogger(name).propagate = False


_configure_logging()

app = FastAPI(title="Student Projects Catalogue API")

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
