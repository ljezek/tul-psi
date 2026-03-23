from __future__ import annotations

import asyncio
import time
from opentelemetry import trace

from observability import metrics as app_metrics


async def call_backend_service(service_name: str, operation: str, delay_ms: int) -> dict[str, str]:
    tracer = trace.get_tracer("tul.psi.http-client")
    with tracer.start_as_current_span("http.client") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("server.address", service_name)
        span.set_attribute("http.route", operation)
        start = time.perf_counter()
        await asyncio.sleep(delay_ms / 1000)
        elapsed_ms = (time.perf_counter() - start) * 1000

        attrs = {"service": service_name, "operation": operation, "status": "ok"}
        if app_metrics.outbound_http_requests_total:
            app_metrics.outbound_http_requests_total.add(1, attributes=attrs)
        if app_metrics.outbound_http_latency_ms:
            app_metrics.outbound_http_latency_ms.record(elapsed_ms, attributes=attrs)

        span.set_attribute("http.status_code", 200)
        span.set_attribute("http.duration_ms", elapsed_ms)

    return {"service": service_name, "operation": operation, "status": "ok"}
