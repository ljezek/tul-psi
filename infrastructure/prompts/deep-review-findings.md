# SPC Deep Review — Findings & Fix Backlog

Full-stack review covering backend (FastAPI/Python), frontend (React/TypeScript), and
infrastructure (Bicep/Azure). Each section below maps to a **single PR** with a coherent scope.

Severity labels: **HIGH** = fix before widening access · **MEDIUM** = fix soon · **LOW** = nice to have

---

## PR 1 — Backend Security Headers & Rate Limiting

**Scope:** `backend/`

### [HIGH] Missing HTTP Security Headers
- `backend/main.py` — No `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`,
  or `Referrer-Policy` headers are set.
- **Fix:** Add a custom `SecurityHeadersMiddleware` (or use `starlette-security`) that injects these
  headers on every response.

### [HIGH] No Rate Limiting on OTP Endpoint
- `backend/api/auth.py` — `/auth/otp/request` has no network-level rate limiting; only an app-level
  5-attempt counter per token. A malicious client can hammer the endpoint freely.
- **Fix:** Add [SlowAPI](https://pypi.org/project/slowapi/) (FastAPI-compatible); limit OTP request
  to ≤5 requests/minute per IP.

### [MEDIUM] URL Validation Missing on Project Fields
- `backend/schemas/projects.py` — `github_url` and `live_url` are plain `str | None`.
  Accepts `javascript:`, `file://`, or otherwise malformed URLs that the frontend renders as links.
- **Fix:** Change both fields to `pydantic.HttpUrl | None = None`.

---

## PR 2 — CSRF Protection (Backend + Frontend, coordinated)

**Scope:** `backend/api/deps.py`, `backend/api/auth.py`, `frontend/src/api.ts`

### [HIGH] CSRF Double Submit Cookie Not Implemented
- `backend/api/deps.py:36` — Explicit TODO: "Replace the CSRF mock below with real Double Submit
  Cookie validation once the frontend sends the `X-XSRF-Token` header."
- `frontend/src/api.ts:43` — Matching TODO: "Add XSRF token header for state-changing requests."
- **Fix (backend):** On login, set a `XSRF-TOKEN` cookie (non-HttpOnly, SameSite=Strict).
  Validate the `X-XSRF-Token` request header against the cookie value for all POST/PATCH/DELETE.
- **Fix (frontend):** Read the `XSRF-TOKEN` cookie and send it as `X-XSRF-Token` header in
  `apiFetch()` for all state-changing requests.

---

## PR 3 — Backend Code Quality: Exception Handling & API Contract

**Scope:** `backend/api/`, `backend/settings.py`, `backend/services/auth_service.py`

### [HIGH] Overly Broad Exception Catching
- `backend/api/courses.py`, `backend/api/projects.py`, `backend/api/users.py` — Every route handler
  wraps its body in `except Exception:` and returns a generic 500 with no traceback in logs.
  Programming errors (AttributeError, KeyError) are silently swallowed.
- **Fix:** Catch specific exceptions (`SQLAlchemyError`, custom domain errors). Register a global
  FastAPI `exception_handler` for unhandled errors that logs the full traceback before returning 500.

### [MEDIUM] POST Returns 201 on Evaluation Upsert Update
- `backend/api/projects.py:345` — `save_project_evaluation` always returns `HTTP 201 Created`, even
  when it updates an existing record.
- **Fix:** Detect insert vs. update (e.g. via a returned flag from the service layer) and return
  `200 OK` on update, `201 Created` on insert. Alternatively, change the verb to `PUT`.

### [MEDIUM] Missing Azure Managed Identity Config Validation
- `backend/settings.py` — No validator ensures `azure_client_id` is provided when
  `azure_managed_identity_enabled=True`; misconfiguration fails silently at runtime.
- **Fix:**
  ```python
  @model_validator(mode="after")
  def _validate_azure_mi(self) -> "Settings":
      if self.azure_managed_identity_enabled and not self.azure_client_id:
          raise ValueError("azure_client_id required when azure_managed_identity_enabled=True")
      return self
  ```

### [LOW] Magic Numbers Not in Config
- `backend/services/auth_service.py:20,23` — `_MAX_OTP_ATTEMPTS = 5`, `_JWT_TTL_HOURS = 8` are
  module-level constants; cannot be tuned without code changes.
- **Fix:** Move to `settings.py` as `otp_max_attempts: int = 5` and `jwt_ttl_hours: int = 8`.

### [LOW] bcrypt Blocking the Async Event Loop
- `backend/services/auth_service.py` — `bcrypt.hashpw()` / `bcrypt.gensalt()` run synchronously
  in async request handlers; will degrade event-loop throughput under load.
- **Fix:** `await asyncio.to_thread(bcrypt.hashpw, otp.encode(), bcrypt.gensalt())`.

### [LOW] Unused `greenlet` Dependency
- `backend/requirements.txt` — `greenlet==3.0.3` appears unnecessary with asyncpg's native async
  driver.
- **Fix:** Remove; run full test suite to confirm no breakage.

---

## PR 4 — Backend Database: Indexes & Connection Pool

**Scope:** `backend/migrations/versions/` (new file), `backend/db/session.py`

### [MEDIUM] Missing Database Indexes
- `backend/db/projects.py:85` — `project.technologies @>` JSONB operator with no GIN index
  → full table scan on every technology filter.
- No composite BTree index on `(course_id, academic_year, term)` despite that triple appearing
  in the multi-filter list query.
- **Fix:** New Alembic migration:
  ```python
  op.create_index('idx_project_technologies_gin', 'project',
                  ['technologies'], postgresql_using='gin')
  op.create_index('idx_project_course_year_term', 'project',
                  ['course_id', 'academic_year', 'term'], postgresql_using='btree')
  ```

### [LOW] No SQLAlchemy Connection Pool Limits
- `backend/db/session.py` — No explicit `pool_size`, `max_overflow`, or `pool_recycle`.
  PostgreSQL `Standard_B1ms` defaults to 50 `max_connections`; the backend could exhaust them
  under moderate load.
- **Fix:** Set `pool_size=5, max_overflow=10, pool_recycle=300` in the engine factory.

---

## PR 5 — Backend Integration Tests

**Scope:** `backend/tests/integration/` (new directory)

### [MEDIUM] No End-to-End Integration Tests
- 185+ unit tests exist, but no cross-route lifecycle flows are tested.
  Regressions in multi-step operations (create project → add member → evaluate → unlock results)
  can only be caught manually.
- **Fix:** Add 3–5 integration tests that run against a real test database transaction and exercise
  full request/response chains through the FastAPI `TestClient`.

---

## PR 6 — Frontend: Request Timeouts, ProtectedRoute Tests & Error UI

**Scope:** `frontend/src/api.ts`, `frontend/src/components/ProtectedRoute.tsx`, various pages

### [HIGH] No Request Timeouts or AbortController
- `frontend/src/api.ts` — All `fetch` calls have no timeout or cancellation signal.
  A hung backend request blocks the UI indefinitely; unmounted components leave dangling requests.
- **Fix:** Add `AbortController` + 30-second timeout inside `apiFetch()`; pass `signal` to `fetch`.
  Call `controller.abort()` in `useEffect` cleanup functions on page components.

### [HIGH] ProtectedRoute Has No Tests
- `frontend/src/components/ProtectedRoute.tsx` — The authentication gate for all protected pages
  has no test file at all.
- **Fix:** Add tests for: authenticated user can reach protected page, unauthenticated user is
  redirected to `/login`, wrong-role user is rejected.

### [MEDIUM] Error Handling Inconsistency
- `frontend/src/pages/student/StudentHome.tsx`, `frontend/src/pages/admin/UserManagement.tsx` —
  Use `alert()` for errors. Other pages use the `<ErrorMessage>` component.
- **Fix:** Replace all `alert()` calls with `<ErrorMessage>` (or a toast notification system).

### [MEDIUM] Race Condition in Dashboard Data Fetching
- `frontend/src/pages/Dashboard.tsx` — `fetchData()` is triggered on every `user` context change
  with no in-flight guard; rapid auth-context updates can fire concurrent overlapping requests.
- **Fix:** Add a `useRef` in-flight flag, or adopt React Query for automatic deduplication.

### [LOW] Duplicate Email Normalization
- `.toLowerCase().trim()` repeated in `Login.tsx` and `UserManagement.tsx`.
- **Fix:** Extract to `frontend/src/utils/normalizeEmail.ts`.

---

## PR 7 — Frontend: Accessibility Fixes

**Scope:** `frontend/src/components/Modal.tsx`, `frontend/src/components/LoadingSpinner.tsx`,
form components

### [MEDIUM] A11y Gaps
- Form error messages are not linked to their inputs via `aria-describedby`; screen readers
  cannot associate the error with the field.
- `<LoadingSpinner>` lacks `aria-live="polite"` — screen readers don't announce when loading begins.
- Modal backdrop `<div>` is missing `aria-hidden="true"` — screen readers may read hidden content.
- **Fix (LoadingSpinner):**
  ```tsx
  <div role="status" aria-live="polite" aria-busy="true">
    {/* spinner markup */}
  </div>
  ```
- **Fix (Modal backdrop):** Add `aria-hidden="true"` to the overlay `<div>`.
- **Fix (form errors):** Link each error message element via `aria-describedby` on the input.

---

## PR 8 — Frontend: Bundle Analysis & Minor Cleanup

**Scope:** `frontend/`

### [LOW] No Bundle Size Tracking
- No `vite-plugin-visualizer`; bundle regressions go undetected.
- **Fix:** Add `rollup-plugin-visualizer` as a dev dependency; invoke it in `vite.config.ts`
  (write `stats.html` on build, but don't block CI on it).

### [LOW] Duplicate Email Normalization
- Already covered in PR 6 — include here if PR 6 doesn't exist yet.

---

## PR 9 — Infrastructure: Database Backup & Resource Locks

**Scope:** `infrastructure/modules/database.bicep`, `infrastructure/modules/acr.bicep`

### [HIGH] No Database Backup Configuration
- `infrastructure/modules/database.bicep:73-97` — No `backup` block; PostgreSQL has no explicit
  retention policy. The Burstable SKU supports local-redundant automated backup at no extra cost.
- **Fix:** Add to the `postgres` resource:
  ```bicep
  backup: {
    backupRetentionDays: 7
    geoRedundantBackup: 'Disabled'
  }
  ```
  *(Geo-redundant backup requires General Purpose tier; not needed for this project.)*

### [HIGH] No CanNotDelete Locks on Critical Resources
- PostgreSQL server and ACR have no resource locks; accidental deletion from the portal destroys
  production data and images with no safety net.
- **Fix:** Add to `database.bicep` and `acr.bicep`:
  ```bicep
  resource postgresLock 'Microsoft.Authorization/locks@2020-05-01' = {
    name: 'lock-${postgres.name}'
    scope: postgres
    properties: { level: 'CanNotDelete', notes: 'Prevent accidental deletion of production DB' }
  }
  ```

### [MEDIUM] Overly Permissive Bootstrap Identity Roles
- `infrastructure/modules/database.bicep:43-51` — The DB-setup identity is assigned
  `StorageAccountContributor` (full control over storage config and keys) on the storage account.
  Only blob-level access is needed to upload and run the bootstrap script.
- **Fix:** Remove the `storageContributor` role assignment; retain only `blobContributor`.

---

## PR 10 — Infrastructure: Resource Tags & Log Analytics Retention

**Scope:** `infrastructure/environment.bicep`, `infrastructure/shared.bicep`,
`infrastructure/modules/*.bicep`, `infrastructure/modules/monitoring.bicep`

### [HIGH] No Resource Tags on Any Azure Resource
- Zero `tags` properties across all Bicep files; cost allocation and resource grouping in Azure
  Cost Management are impossible.
- **Fix:** Add a `tags` parameter to `environment.bicep` and `shared.bicep`; thread it through all
  module calls; apply `tags: tags` to every resource. Minimum useful tag set:
  ```bicep
  param tags object = {
    project: 'spc'
    env: env
    managedBy: 'bicep'
  }
  ```

### [LOW] Log Analytics Retention Too Short
- `infrastructure/modules/monitoring.bicep` — Default 30-day retention may be too short for
  post-incident investigations.
- **Fix:** Increase to 90 days for the production workspace (gate on `env == 'prod'`).

---

## PR 11 — Infrastructure: Health Probes, Diagnostics & CI/CD Hardening

**Scope:** `infrastructure/modules/compute.bicep`, `backend/Dockerfile`,
`.github/workflows/infrastructure.yml`, `.github/workflows/backend-dev.yml`,
`.github/workflows/frontend-dev.yml`

### [HIGH] No Health Probes on Backend Container App
- `infrastructure/modules/compute.bicep:80-154` — No liveness probe configured.
  A crashed or deadlocked container stays in rotation until manually restarted.
- **Fix (Bicep):** Add inside the backend container template:
  ```bicep
  probes: [
    { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 30,
      failureThreshold: 3 }
  ]
  ```
- **Fix (Dockerfile):** Add `HEALTHCHECK CMD curl -sf http://localhost:8000/health || exit 1`.

### [HIGH] No Job Timeouts in GitHub Actions Workflows
- All three workflow files have no `timeout-minutes`; a hung step runs for 6 hours (GitHub default),
  consuming expensive runner minutes and blocking branch protection.
- **Fix:** Add `timeout-minutes: 30` to every `jobs.<id>` block in:
  `.github/workflows/infrastructure.yml`, `backend-dev.yml`, `frontend-dev.yml`.

### [MEDIUM] Missing Platform-Level Diagnostics for Container Apps
- The OTel sidecar captures application traces/metrics. It does **not** capture platform events:
  container crashes, OOM kills, cold-start timing, or scale-in/out events.
  These are only available through Azure Monitor diagnostic settings.
- **Fix:** Add `Microsoft.Insights/diagnosticSettings` to `compute.bicep` for the backend app,
  sending `ContainerAppConsoleLogs` and `ContainerAppSystemLogs` to the existing Log Analytics
  workspace.

### [MEDIUM] No Rollback Strategy in Backend CI/CD
- `backend-dev.yml` — If `az containerapp update` fails after a migration has already been applied,
  the app is stuck on the old image with a newer schema.
- **Fix:** Capture the active revision name before the update; re-activate it on failure:
  ```bash
  PREV=$(az containerapp revision list --name $APP --resource-group $RG \
           --query "[?properties.active].name | [0]" -o tsv)
  az containerapp update ... || \
    az containerapp revision activate --revision "$PREV" --name $APP --resource-group $RG
  ```

### [MEDIUM] OTEL Collector CORS Allows All Origins
- `infrastructure/monitoring/otel-collector-config.azure.yaml:9` — `allowed_origins: ["*"]`.
- **Fix:** Replace `*` with the backend container's internal address (e.g. `http://localhost:8000`).

---

## PR 12 — Infrastructure: pgAdmin Security & Scale-to-Zero Documentation

**Scope:** `infrastructure/modules/compute.bicep`, `infrastructure/README.md`

### [MEDIUM] pgAdmin Falls Back to Unauthenticated Access
- When `PGADMIN_AAD_CLIENT_ID` / `PGADMIN_AAD_CLIENT_SECRET` are absent from GitHub secrets,
  `deployPgadminAuth` is `false` and pgAdmin is exposed to the internet without authentication.
- **Fix:** Either (a) gate the entire pgAdmin Container App resource on `deployPgadminAuth` so it
  simply is not deployed when secrets are missing, or (b) make the deployment fail explicitly if
  the debug tools flag is true but auth secrets are absent.

### [MEDIUM] Scale-to-Zero Cold Starts — Demo Day Procedure Undocumented
- `minReplicas: 0` is intentional for cost. Cold starts cause ~10–30 s latency on the first
  request, which is disruptive during a live demo.
- **Fix:** Add a "Demo Day" section to `infrastructure/README.md`:
  ```bash
  # Before demo — eliminate cold starts:
  az containerapp update --name app-spc-dev --resource-group rg-spc-dev --min-replicas 1
  # After demo — restore cost-saving default:
  az containerapp update --name app-spc-dev --resource-group rg-spc-dev --min-replicas 0
  ```

### Future Work (document only, no implementation planned)
- **Azure Key Vault:** JWT_SECRET and pgAdmin credentials flow through GitHub Secrets with no
  rotation mechanism. Long-term: store them in Key Vault and reference from Bicep.
- **ACR Private Endpoint:** Basic SKU does not support private link; ACR is internet-facing.
  Long-term: upgrade to Standard SKU and add a private endpoint.
