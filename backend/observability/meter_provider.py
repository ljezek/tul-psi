from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader

from settings import Settings


prometheus_reader: PrometheusMetricReader | None = None


def setup_meter_provider(settings: Settings) -> None:
    global prometheus_reader

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.otel_service_version,
            "deployment.environment": settings.app_env,
        }
    )

    prometheus_reader = PrometheusMetricReader()

    meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
    metrics.set_meter_provider(meter_provider)
