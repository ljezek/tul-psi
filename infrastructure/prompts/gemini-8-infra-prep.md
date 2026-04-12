# Infrastructure Preparation Plan (SPC)

This document outlines the foundational work required **before** creating Azure resources. We follow a "Local-First" approach to ensure the application is container-ready and observable.

## 1. Backend Dockerization
Before pushing to Azure Container Registry, we must ensure the backend is correctly containerized.

### 📋 TODO: Create `backend/Dockerfile`
Create a multi-stage build:
1.  **Build Stage:** Install dependencies and build wheels.
2.  **Runtime Stage:** A slim Python 3.12 image, non-root user (`appuser`), and OTel instrumentation enabled.

## 2. Local Monitoring & Observability Stack
We use a 2-container local stack to mirror cloud behavior without the complexity of Azure.

### 📋 TODO: Create Root `docker-compose.yaml`

In the database setup respect the existing database/docker-compose.yml settings (users & disk).

```yaml
services:
  # The "Shared Stack": Prometheus, Jaeger, Grafana, Loki (All-in-one)
  monitoring-stack:
    image: grafana/otel-lgtm:0.6.0
    ports:
      - "3001:3000"   # Grafana UI
      - "4317:4317"   # OTLP gRPC (internal)
      - "16686:16686" # Jaeger UI
    environment:
      - OTEL_METRIC_EXPORT_INTERVAL=5000

  # Standalone OTel Collector (Mirrors Azure Sidecar)
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.111.0
    volumes:
      - ./infrastructure/otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml
    command: ["--config=/etc/otelcol-contrib/config.yaml"]
    depends_on:
      - monitoring-stack

  # Database
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: spc
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  # Backend (Containerized with Hot-Reload)
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app  # Bind mount for --reload
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/spc
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - LOG_LEVEL=debug
    ports:
      - "8000:8000"
    depends_on:
      - db
      - otel-collector

  # Frontend (Optional: For Full-Stack Demo)
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

```      

## 3. Development Workflow: Dual-Mode
To balance "Parity" and "Speed", we support two modes:

### Mode A: Full-Stack (Containerized)
- **Command:** `docker compose up --build`
- **Use Case:** Verifying migrations, OTel traces, or demonstrating the whole system.
- **Note:** This is the only way to test the OTel Sidecar pattern locally.

### Mode B: Rapid Dev (Native + Docker Hybrid)
This is the **preferred daily workflow**:
1.  **Infrastructure:** `docker compose up db otel-collector monitoring-stack` (Start only the "boring" stuff).
2.  **Backend:** `./backend/start.ps1` (Run locally for fast restarts and debugging).
3.  **Frontend:** `cd frontend; npm run dev` (Run natively for the fastest HMR and easiest debugging).


## 4. Backend: Azure Managed Identity Support
Add `azure-identity` to `backend/requirements.txt` and update `backend/db/session.py` to support Entra ID tokens when `AZURE_MANAGED_IDENTITY_ENABLED=true`.

## 5. OTel Collector Configuration (`infrastructure/otel-collector-config.yaml`)
Configure receivers for OTLP and exporters for both the local `monitoring-stack` and the future Azure `azuremonitor`.