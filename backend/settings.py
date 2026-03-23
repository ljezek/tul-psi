from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "tul-psi-monitoring-sample"
    app_env: str = "local"
    log_level: str = "INFO"

    projects_data_file: str = "data/projects.json"
    simulated_db_delay_ms: int = 35
    simulated_http_delay_ms: int = 55

    otel_enabled: bool = True
    otel_service_name: str = "tul-psi-fastapi-sample"
    otel_service_version: str = "0.1.0"

    otel_traces_exporter: str = "otlp"
    otel_metrics_exporter: str = "prometheus"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_insecure: bool = True

    otel_traces_sampler: str = "parentbased_traceidratio"
    otel_traces_sampler_arg: float = 1.0

    otel_enable_azure_monitor: bool = False
    azure_monitor_connection_string: str = ""

    metrics_path: str = "/metrics"


@lru_cache
def get_settings() -> Settings:
    return Settings()
