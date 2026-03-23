from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from pathlib import Path
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from models.project import Project
from observability import metrics as app_metrics

logger = logging.getLogger(__name__)


async def load_projects_from_db(
    data_file: str,
    delay_ms: int,
    academic_year: str | None = None,
    subject: str | None = None,
    error_rate: float = 0.0,
) -> list[Project]:
    tracer = trace.get_tracer("tul.psi.db")
    with tracer.start_as_current_span("db.load_projects") as span:
        span.set_attribute("db.system", "mock-json")
        span.set_attribute("db.operation", "load_projects")
        span.set_attribute("db.data_file", data_file)
        span.set_attribute("filters.academic_year", academic_year or "")
        span.set_attribute("filters.subject", subject or "")

        actual_delay_ms = delay_ms * random.uniform(1.0, 5.0)
        start = time.perf_counter()
        await asyncio.sleep(actual_delay_ms / 1000)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if random.random() < error_rate:
            error_msg = "Cannot load projects from database"
            attrs = {"query_name": "load_projects", "db_system": "mock-json", "status": "error"}
            if app_metrics.db_queries_total:
                app_metrics.db_queries_total.add(1, attributes=attrs)
            if app_metrics.db_query_latency_ms:
                app_metrics.db_query_latency_ms.record(elapsed_ms, attributes=attrs)
            span.set_attribute("db.duration_ms", elapsed_ms)
            span.set_status(StatusCode.ERROR, error_msg)
            exc = RuntimeError(f"[500] {error_msg}")
            span.record_exception(exc)
            logger.error(
                "load_projects_from_db_failed",
                extra={"data_file": data_file, "error": error_msg},
            )
            raise exc

        file_path = Path(data_file)
        with file_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)

        items = payload.get("projects", []) if isinstance(payload, dict) else []
        projects = [
            Project(
                id=row["id"],
                title=row["title"],
                academic_year=row["academicYear"],
                subject=row["subject"],
                technologies=row.get("technologies", []),
            )
            for row in items
            if (not academic_year or row["academicYear"] == academic_year)
            and (not subject or row["subject"].lower() == subject.lower())
        ]

        elapsed_ms = (time.perf_counter() - start) * 1000
        attrs = {"query_name": "load_projects", "db_system": "mock-json"}
        if app_metrics.db_queries_total:
            app_metrics.db_queries_total.add(1, attributes=attrs)
        if app_metrics.db_query_latency_ms:
            app_metrics.db_query_latency_ms.record(elapsed_ms, attributes=attrs)

        span.set_attribute("db.duration_ms", elapsed_ms)
        span.set_attribute("db.projects_loaded", len(projects))
        span.set_attribute("db.projects_after_filter", len(projects))

    return projects
