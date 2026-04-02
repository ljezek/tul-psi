from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from settings import Settings


def setup_meter_provider(settings: Settings) -> None:
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.otel_service_version,
            "deployment.environment": settings.app_env,
        }
    )

    exporter = OTLPMetricExporter(
        endpoint=f"{settings.otel_exporter_otlp_endpoint}/v1/metrics",
    )
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=15000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
