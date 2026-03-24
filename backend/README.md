# FastAPI Monitoring and Tracing Sample

This sample backend demonstrates best practices for:

- Health check (`/health`)
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
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Then open:

- `http://localhost:8001/projects`
- `http://localhost:8001/health`

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

- **OTel Collector** receives OTLP (HTTP/gRPC) from the app on ports `4317`/`4318`
- Collector forwards **traces** to Jaeger via OTLP gRPC
- Collector pushes **metrics** to Prometheus via remote write
- Jaeger UI: trace visualisation
- Prometheus: metrics storage
- Grafana: pre-provisioned dashboards with Prometheus and Jaeger datasources

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

Metrics are pushed to the OTel Collector via OTLP and forwarded to Prometheus via remote write — no pull endpoint is exposed.

## Simulated Behaviour

All fake operations apply a randomised delay (`uniform(1x, 5x)` of the configured baseline)
to simulate realistic latency variance.

Error injection is controlled by these settings (default `0.10` = 10%):

| Setting | Effect |
|---|---|
| `DB_ERROR_RATE` | `load_projects_from_db` raises a 500 error |
| `ENRICH_ERROR_RATE` | `enrich_project_info` raises a 500 error |

Errors are propagated to the caller and result in an HTTP 500 response. The
`/health` endpoint always bypasses error injection.

## Tracing

Tracing uses OTLP HTTP export and can be visualised in Jaeger.

To generate traces:

```bash
curl -H "X-Client-Type: mobile" "http://localhost:8001/projects?subject=PSI"
curl -H "X-Client-Type: web" "http://localhost:8001/projects?academic_year=2024/25"
curl -H "X-Client-Type: api" "http://localhost:8001/health"
```

Then inspect traces in Jaeger by service name `tul-psi-fastapi-sample`.

Each successful `/projects` request produces three nested spans:
`projects_service.get_projects` → `db.load_projects` + `http.enrich_project` (one per project).

## Azure Compatibility Notes

The app emits all signals (traces and metrics) to the OTel Collector via OTLP.
To route to Azure Monitor, only the **Collector config** changes — no app code changes required:

- Add the `azuremonitor` exporter to `monitoring/otelcollector/config.yaml`
- Set the App Insights connection string in the Collector's environment
- Add the exporter to the `traces` and `metrics` pipelines
