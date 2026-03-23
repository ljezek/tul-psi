from __future__ import annotations

import asyncio
import time
from opentelemetry import trace

from observability.metrics import db_queries_total, db_query_latency_ms


async def simulate_query(query_name: str, delay_ms: int) -> dict[str, str]:
    tracer = trace.get_tracer("tul.psi.db")
    with tracer.start_as_current_span("db.query") as span:
        span.set_attribute("db.system", "mock-json")
        span.set_attribute("db.operation", query_name)
        start = time.perf_counter()
        await asyncio.sleep(delay_ms / 1000)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if db_queries_total:
            db_queries_total.add(1, attributes={"query_name": query_name, "db_system": "mock-json"})
        if db_query_latency_ms:
            db_query_latency_ms.record(
                elapsed_ms,
                attributes={"query_name": query_name, "db_system": "mock-json"},
            )

        span.set_attribute("db.duration_ms", elapsed_ms)

    return {"query_name": query_name}
