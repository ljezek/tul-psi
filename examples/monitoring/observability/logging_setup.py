from __future__ import annotations

import logging
import sys
from pythonjsonlogger import jsonlogger
from opentelemetry import trace


class OtelTraceJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        current_span = trace.get_current_span()
        span_ctx = current_span.get_span_context()
        if span_ctx and span_ctx.is_valid:
            log_record["trace_id"] = format(span_ctx.trace_id, "032x")
            log_record["span_id"] = format(span_ctx.span_id, "016x")
        log_record["logger"] = record.name
        log_record["severity"] = record.levelname


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = OtelTraceJsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    logging.getLogger("uvicorn.access").setLevel(level.upper())
    logging.getLogger("uvicorn.error").setLevel(level.upper())
