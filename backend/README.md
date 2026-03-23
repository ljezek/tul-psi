# FastAPI Monitoring and Tracing Sample

This sample backend demonstrates best practices for:

- Health checks (`/health/live`, `/health/ready`)
- Structured JSON logging for Log Analytics export
- Metrics for RPS, error rate and latency (inbound and outbound)
- End-to-end request tracing with OpenTelemetry

It reads project data from `backend/db/fake_projects.json`, simulates outbound HTTP
and DB calls (with configurable delays), and injects random errors to demonstrate
error-rate monitoring.

## Run Backend

```bash
cd backend
../.venv/Scripts/Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --app-dir . --port 8001
```

Recommended `backend/.env` for local monitoring:

```env
APP_ENV=local
PROJECTS_DATA_FILE=db/fake_projects.json
SIMULATED_DB_DELAY_MS=35
SIMULATED_HTTP_DELAY_MS=55
DB_ERROR_RATE=0.10
ENRICH_ERROR_RATE=0.10
OTEL_ENABLED=true
OTEL_TRACES_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Then open:

- `http://localhost:8001/projects`
- `http://localhost:8001/health/live`
- `http://localhost:8001/health/ready`

## Local Monitoring Stack

Run the local observability stack from `backend/monitoring`:

```bash
cd monitoring
docker compose up -d
```

Services:

- Jaeger UI: `http://localhost:16686`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (`admin` / `admin`)

This setup is intended for local teaching demos:

- Jaeger receives OTLP HTTP traces on port `4318`
- Prometheus scrapes the backend `http://host.docker.internal:8001/metrics` endpoint
- Grafana is pre-provisioned with Prometheus and Jaeger datasources
- A starter dashboard is included in Grafana

## Metrics

Inbound metrics recorded by the app:

- `http_server_requests_total` — labelled by `http_route` and `http_status_code`
- `http_server_request_duration` — labelled by `http_route`

Outbound metrics recorded by the app:

- `http_client_requests_total` — labelled by `service`, `operation`, and `status` (`ok`/`error`)
- `http_client_request_duration` — labelled by `service` and `operation`
- `db_queries_total` — labelled by `query_name`, `db_system`, and `status` (`ok`/`error`)
- `db_query_duration` — labelled by `query_name`

Default metrics reported by OpenTelemetry:

- `http_server_active_requests`
- `http_server_response_size`
- `http_server_duration`
- `python_gc_*`

The backend exposes a dedicated `/metrics` endpoint for the standard Prometheus pull model.

## Simulated Behaviour

All fake operations apply a randomised delay (`uniform(1x, 5x)` of the configured baseline)
to simulate realistic latency variance.

Error injection is controlled by these settings (default `0.10` = 10%):

| Setting | Effect |
|---|---|
| `DB_ERROR_RATE` | `load_projects_from_db` raises a 500 error |
| `ENRICH_ERROR_RATE` | `enrich_project_info` raises a 500 error |

Errors are propagated to the caller and result in an HTTP 500 response. The readiness
check (`/health/ready`) always bypasses error injection.

## Tracing

Tracing uses OTLP HTTP export and can be visualised in Jaeger.

To generate traces:

```bash
curl -H "X-Client-Type: mobile" "http://localhost:8001/projects?subject=PSI"
curl -H "X-Client-Type: web" "http://localhost:8001/projects?academic_year=2024/25"
curl -H "X-Client-Type: api" "http://localhost:8001/health/ready"
```

Then inspect traces in Jaeger by service name `tul-psi-fastapi-sample`.

Each successful `/projects` request produces three nested spans:
`projects_service.get_projects` → `db.load_projects` + `http.enrich_project` (one per project).

## Azure Compatibility Notes

For Azure App Service + Application Insights / Log Analytics:

- Keep using OpenTelemetry instrumentation in code.
- Set `OTEL_ENABLE_AZURE_MONITOR=true`.
- Set `AZURE_MONITOR_CONNECTION_STRING` to your App Insights connection string.
- Keep structured JSON logs; add custom dimensions using `extra={...}` fields.
