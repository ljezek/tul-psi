# Observability & Monitoring Guide

This document describes the observability stack and monitoring strategy for the Student Projects Catalogue (SPC) in Azure.

## Overview
The application uses **OpenTelemetry (OTel)** for comprehensive observability.
* **Backend:** FastAPI is instrumented with the Python OTel SDK, capturing traces, metrics, and structured JSON logs. Telemetry is sent via OTLP to an OpenTelemetry Collector sidecar running in the same Container App environment, which exports it to **Azure Application Insights**.
* **Frontend:** The React SPA is instrumented with the Azure Monitor OpenTelemetry Browser SDK. It sends Real User Monitoring (RUM) data (page loads, JS errors, frontend latency, network calls) directly to Application Insights using an ingestion connection string.

All data is stored in a **Log Analytics Workspace** underlying the Application Insights instance.

---

## 1. Metrics & Graphs (Backend)

Because we use OpenTelemetry metrics exported to Application Insights, they appear as "Custom Metrics" in Azure.

### How to view them:
1. Navigate to your Application Insights resource (`ai-spc-<env>`) in the Azure Portal.
2. Click on **Metrics** in the left sidebar.
3. In the "Metric Namespace" dropdown, select **azure.applicationinsights** (or Custom if separated). Often OTel metrics appear under "Log-based metrics" or "Custom metrics".
4. Select the metric you want to graph:
    * `http_server_requests_total` (RPC Server Requests)
    * `http_server_request_duration` (RPC Server Latency)
    * `http_client_requests_total` (RPC Client / Outbound Requests)
    * `db_queries_total` (Database Requests)

### Native Experiences
Alternatively, use the native Azure UI which interprets OTel spans automatically:
* **Performance Blade:** Shows P50, P95, P99 duration for all backend endpoints (`GET /api/v1/projects`, etc.) and database queries.
* **Failures Blade:** Shows 5xx errors and exceptions grouped by endpoint.

---

## 2. Frontend Graphs (Real User Monitoring)

Frontend telemetry is sent directly from the user's browser.

### How to view them:
1. In Application Insights, go to the **Performance** blade.
2. Toggle the switch at the top from "Server" to **"Browser"**.
3. You will see metrics for:
    * Page Load Time (Network, DOM Processing, etc.)
    * AJAX calls (latency of frontend calling the FastAPI backend)
4. Go to the **Failures** blade and toggle to **"Browser"** to see JavaScript exceptions and failed AJAX calls.
5. **Usage:** Explore the "Users", "Sessions", and "Events" blades under the "Usage" section to see adoption and user flows.

### Security Trade-off: Frontend Connection String
The frontend requires the `VITE_APPINSIGHTS_CONNECTION_STRING` to send telemetry. Because this string is public in the browser, a malicious user could theoretically spoof telemetry to inflate Azure ingestion costs.
* **Current Mitigation:** A single shared Application Insights instance with a **Daily Volume Cap** (e.g. 0.5 GB/day) can be configured on the Log Analytics Workspace. This limits the total cost exposure but drops all telemetry (including backend) if the cap is reached. This is an accepted risk for a low-traffic academic project.

---

## 3. Application Logs

Backend logs are formatted as structured JSON and enriched with `trace_id` and `span_id`.

### How to query them:
1. In Application Insights, click on **Logs**.
2. Run Kusto Query Language (KQL) queries against the `AppTraces` or `AppExceptions` tables.

**Useful KQL Queries:**

* **View all recent application logs:**
  ```kusto
  AppTraces
  | sort by TimeGenerated desc
  | limit 100
  ```

* **Filter logs by severity (e.g., Warnings & Errors):**
  ```kusto
  AppTraces
  | where SeverityLevel >= 2 // 2=Warning, 3=Error, 4=Critical
  | sort by TimeGenerated desc
  ```

* **Find logs for a specific request/trace:**
  ```kusto
  AppTraces
  | where OperationId == "<insert-trace-id-here>"
  | sort by TimeGenerated asc
  ```

* **Parse custom JSON properties from the log message:**
  ```kusto
  AppTraces
  | extend parsed = parse_json(Properties)
  | project TimeGenerated, Message, SeverityLevel, parsed.user_id, parsed.environment
  ```

---

## 4. Traces & Application Map

Traces represent the end-to-end journey of a single request. Because both Frontend and Backend share the same Application Insights instance, their traces are correlated automatically.

### How to view them:
1. **Application Map:** Click "Application Map" in the left sidebar. This provides a visual topology of the Frontend, Backend, and PostgreSQL database, showing average latency and failure rates between nodes.
2. **Transaction Search:** Click "Transaction search" to find specific requests.
3. **End-to-End Transaction Details:** When you click on a slow or failed request in the "Performance" or "Failures" blades, you will see the waterfall view. This view shows:
    * The frontend browser action (e.g., click)
    * The network transit time
    * The FastAPI route execution
    * The exact PostgreSQL query executed (and its duration)

---

## 5. Alerts

We use Azure Monitor **Scheduled Query Rules (Log Search Alerts)** to detect application degradation gracefully, specifically handling the fact that the application scales to 0 (which causes slow 10s "cold start" requests).

Alerts are provisioned automatically via Bicep (`infrastructure/modules/alerts.bicep`). Notifications are sent via email to the address configured in the `alertsEmail` Bicep parameter.

### Configured Alerts:

1. **High Error Rate (5xx)**
    * **Trigger:** 3 or more HTTP 5xx errors on a *single endpoint* within a 5-minute window.
    * **Why:** Identifies broken routes without alerting on a single random blip.
    * **How to tune:** In Azure Portal -> Alerts -> Alert Rules -> "High Error Rate (5xx)" -> Edit the KQL query or the "Threshold" value.

2. **High Sustained Latency (P95)**
    * **Trigger:** The 95th percentile (P95) latency for a specific endpoint is > 1000ms over a 5-minute window, *AND* the endpoint received at least 5 requests.
    * **Why:** Detects sustained slowdowns. Requiring 5 requests prevents the 10-second cold-start from triggering an alert on low-traffic endpoints.
    * **How to tune:** In Azure Portal -> Alerts -> Alert Rules -> "High Sustained Latency (P95)" -> Edit the KQL query or the Threshold (> 1000).

### Modifying Alert Thresholds permanently
To change the thresholds permanently across deployments, edit the KQL queries and `threshold` properties directly in `infrastructure/modules/alerts.bicep` and redeploy the infrastructure pipeline.
