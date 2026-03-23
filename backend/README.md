# FastAPI Monitoring and Tracing Sample

This sample backend demonstrates best practices for:

- Health checks (`/health/live`, `/health/ready`)
- Structured JSON logging for Log Analytics export
- Metrics for RPS and latency (inbound and outbound)
- End-to-end request tracing with OpenTelemetry

It reads project data from `../data/projects.json` and simulates outbound HTTP and DB calls.

## Run

```bash
cd backend
py -3.13 -m venv ../.venv
# Windows PowerShell
../.venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --app-dir . --port 8001
```

Then open:

- `http://localhost:8001/projects`
- `http://localhost:8001/health/live`
- `http://localhost:8001/health/ready`

## Metrics

Inbound metrics:

- `http_server_requests_total`
- `http_server_request_duration_ms`

Outbound metrics:

- `http_client_requests_total`
- `http_client_request_duration_ms`
- `db_queries_total`
- `db_query_duration_ms`

Labels include endpoint and client type (`mobile|web|api|unknown`) for inbound requests.

## Tracing

Default uses OTLP exporter and is suitable for local Jaeger/OpenTelemetry Collector.

A simple local path is to run Jaeger all-in-one with OTLP gRPC receiver enabled and set:

- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`

## Azure Compatibility Notes

For Azure App Service + Application Insights / Log Analytics:

- Keep using OpenTelemetry instrumentation in code.
- Set `OTEL_ENABLE_AZURE_MONITOR=true`.
- Set `AZURE_MONITOR_CONNECTION_STRING` to your App Insights connection string.
- Keep structured JSON logs; add custom dimensions using `extra={...}` fields.

## Example Requests

```bash
curl -H "X-Client-Type: mobile" "http://localhost:8001/projects?subject=PSI"
curl -H "X-Client-Type: web" "http://localhost:8001/projects?academic_year=2024/25"
curl -H "X-Client-Type: api" "http://localhost:8001/health/ready"
```
