from __future__ import annotations

import asyncio
import logging
import random
import time
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from observability import metrics as app_metrics

logger = logging.getLogger(__name__)

SERVICE_NAME = "student-profile-service"

STUDENT_NAMES = [
    "Alice Novak",
    "Barbora Horakova",
    "David Prochazka",
    "Eva Blahova",
    "Filip Mares",
    "Gabriela Vesela",
    "Hana Ruzickova",
    "Ivan Cerny",
    "Jana Kovarova",
    "Karel Sykora",
    "Lenka Pospichalova",
    "Martin Dvorak",
    "Nikola Kratka",
    "Ondrej Blazek",
    "Petra Simkova",
]


async def enrich_project_info(
    project_name: str,
    delay_ms: int,
    error_rate: float = 0.10,
) -> dict:
    tracer = trace.get_tracer("tul.psi.http-client")
    with tracer.start_as_current_span("http.enrich_project") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("server.address", SERVICE_NAME)
        span.set_attribute("http.route", "/projects/enrich")
        span.set_attribute("project.name", project_name)

        actual_delay_ms = delay_ms * random.uniform(1.0, 5.0)
        start = time.perf_counter()
        await asyncio.sleep(actual_delay_ms / 1000)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if random.random() < error_rate:
            error_msg = "Cannot load student profile"
            attrs = {
                "service": SERVICE_NAME,
                "operation": "enrich_project",
                "status": "error",
            }
            if app_metrics.outbound_http_requests_total:
                app_metrics.outbound_http_requests_total.add(1, attributes=attrs)
            if app_metrics.outbound_http_latency_ms:
                app_metrics.outbound_http_latency_ms.record(
                    elapsed_ms, attributes=attrs
                )
            span.set_attribute("http.status_code", 500)
            span.set_attribute("http.duration_ms", elapsed_ms)
            span.set_status(StatusCode.ERROR, error_msg)
            exc = RuntimeError(f"[500] {error_msg} for project '{project_name}'")
            span.record_exception(exc)
            logger.error(
                "enrich_project_info_failed",
                extra={
                    "project_name": project_name,
                    "status_code": 500,
                    "error": error_msg,
                },
            )
            raise exc

        attrs = {"service": SERVICE_NAME, "operation": "enrich_project", "status": "ok"}
        if app_metrics.outbound_http_requests_total:
            app_metrics.outbound_http_requests_total.add(1, attributes=attrs)
        if app_metrics.outbound_http_latency_ms:
            app_metrics.outbound_http_latency_ms.record(elapsed_ms, attributes=attrs)

        rng = random.Random(project_name)
        count = rng.randint(3, 5)
        students = rng.sample(STUDENT_NAMES, count)

        span.set_attribute("http.status_code", 200)
        span.set_attribute("http.duration_ms", elapsed_ms)
        span.set_attribute("enrichment.students_count", count)

    return {"project_name": project_name, "status": "ok", "students": students}
