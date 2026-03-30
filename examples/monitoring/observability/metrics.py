from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, Meter

METER_NAME = "tul.psi.monitoring"

_meter: Meter | None = None
http_requests_total: Counter | None = None
http_request_latency_ms: Histogram | None = None
outbound_http_requests_total: Counter | None = None
outbound_http_latency_ms: Histogram | None = None
db_queries_total: Counter | None = None
db_query_latency_ms: Histogram | None = None


def setup_metrics() -> None:
    global _meter
    global http_requests_total, http_request_latency_ms
    global outbound_http_requests_total, outbound_http_latency_ms
    global db_queries_total, db_query_latency_ms

    _meter = metrics.get_meter(METER_NAME)

    http_requests_total = _meter.create_counter(
        name="http_server_requests_total",
        description="Total inbound HTTP requests",
        unit="1",
    )
    http_request_latency_ms = _meter.create_histogram(
        name="http_server_request_duration",
        description="Inbound HTTP request duration",
        unit="ms",
    )
    outbound_http_requests_total = _meter.create_counter(
        name="http_client_requests_total",
        description="Total outbound HTTP requests",
        unit="1",
    )
    outbound_http_latency_ms = _meter.create_histogram(
        name="http_client_request_duration",
        description="Outbound HTTP request duration",
        unit="ms",
    )
    db_queries_total = _meter.create_counter(
        name="db_queries_total",
        description="Total database query calls",
        unit="1",
    )
    db_query_latency_ms = _meter.create_histogram(
        name="db_query_duration",
        description="Database query duration",
        unit="ms",
    )
