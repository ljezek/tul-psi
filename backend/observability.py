from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from settings import get_settings

logger = logging.getLogger(__name__)

# Global flag to prevent double-initialization in some environments
_OTEL_INITIALIZED = False

def setup_otel(app: FastAPI) -> None:
    """Setup OpenTelemetry instrumentation for traces, metrics, and logs."""
    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED:
        logger.info("OpenTelemetry already initialized, skipping setup.")
        return

    settings = get_settings()
    resource = Resource(attributes={SERVICE_NAME: settings.app_name})
    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    # 1. Tracing
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    if otel_endpoint:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otel_endpoint, insecure=True))
        )

    # 2. Metrics
    if otel_endpoint:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=otel_endpoint, insecure=True),
            export_interval_millis=5000,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

    # 3. Logs
    logger_provider = LoggerProvider(resource=resource)
    _logs.set_logger_provider(logger_provider)
    if otel_endpoint:
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter(endpoint=otel_endpoint, insecure=True))
        )

    # Attach OTel Logging Handler to root logger
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)

    # 4. Instrumentations
    FastAPIInstrumentor.instrument_app(app)
    AsyncPGInstrumentor().instrument(capture_parameters=True)
    SQLAlchemyInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False)

    _OTEL_INITIALIZED = True
    logger.info("OpenTelemetry initialization complete.")
