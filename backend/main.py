from __future__ import annotations

import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.health import router as health_router
from api.projects import router as projects_router
from observability import metrics as app_metrics
from observability.context import detect_client_type
from observability.logging_setup import configure_logging
from observability.meter_provider import setup_meter_provider
from observability.tracing import setup_tracing
from settings import get_settings

settings = get_settings()

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

if settings.otel_enabled:
    setup_tracing(settings)
    setup_meter_provider(settings)
app_metrics.setup_metrics()

app = FastAPI(title=settings.app_name)


@app.get(settings.metrics_path, include_in_schema=False)
async def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    start = time.perf_counter()
    client_type = detect_client_type(request)

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        status = 500
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        route = request.url.path
        attrs = {
            "http.method": request.method,
            "http.route": route,
            "http.status_code": status,
            "client.type": client_type,
        }
        if app_metrics.http_requests_total:
            app_metrics.http_requests_total.add(1, attributes=attrs)
        if app_metrics.http_request_latency_ms:
            app_metrics.http_request_latency_ms.record(elapsed_ms, attributes=attrs)

    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_request_error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_type": detect_client_type(request),
            "error_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_type": type(exc).__name__},
    )


app.include_router(health_router)
app.include_router(projects_router)

if settings.otel_enabled:
    FastAPIInstrumentor.instrument_app(app)
