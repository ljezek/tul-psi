from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


from settings import Settings


def setup_tracing(settings: Settings) -> None:
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.otel_service_version,
            "deployment.environment": settings.app_env,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.otel_traces_exporter == "otlp":
        exporter = OTLPSpanExporter(
            endpoint=f"{settings.otel_exporter_otlp_endpoint}/v1/traces",
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    if settings.otel_enable_azure_monitor and settings.azure_monitor_connection_string:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

        azure_exporter = AzureMonitorTraceExporter.from_connection_string(
            settings.azure_monitor_connection_string
        )
        provider.add_span_processor(BatchSpanProcessor(azure_exporter))

    trace.set_tracer_provider(provider)
