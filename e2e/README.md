# E2E Tests — Student Projects Catalogue

Full-stack Playwright tests that run against an ephemeral **Docker Compose** environment (db + backend). The frontend is built and served locally via `vite preview`.

## How it works

- A dedicated `docker-compose.e2e.yaml` spins up PostgreSQL + the FastAPI backend (no observability stack — saves ~20 s startup).
- Alembic migrations and `seed_dev.sql` are applied automatically on startup (via `Dockerfile.dev` / `start.sh`).
- The backend runs with `APP_ENV=e2e` and `E2E_OTP_OVERRIDE=000000`, so every OTP request succeeds with the fixed code `000000` — no real email is sent.
- After the suite, `docker compose down -v` discards the database volume, leaving no residual state.

## Prerequisites

- Docker (with Compose V2 — `docker compose` not `docker-compose`)
- Node.js ≥ 22
- The frontend already built once (`npm ci` inside `frontend/`)

## Running locally

**PowerShell (Windows — recommended)**

```powershell
# 1. Start the backend stack (runs migrations + seed automatically)
#    Add --build on the first run (or after backend code changes) to rebuild the image.
docker compose -f docker-compose.e2e.yaml up -d --wait --build

# 2. Free port 3000 (in case a stale vite preview is still running)
$p = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($p) { Stop-Process -Id $p -Force }

# 3. Build and serve the frontend (new PowerShell window or terminal tab)
cd frontend
npm install
$env:VITE_API_URL="http://localhost:8001"; npm run build
$env:VITE_API_URL="http://localhost:8001"; npx vite preview --port 3000 --strictPort
# Leave this terminal open — Ctrl+C to stop when done.

# 4. Install Playwright and run the tests (original terminal)
cd e2e
npm ci
npx playwright install chromium
npx playwright test

# 5. (Optional) Open the HTML report
npx playwright show-report

# 6. Tear down and remove the database volume
cd ..
docker compose -f docker-compose.e2e.yaml down -v
```

<details>
<summary>Bash / WSL</summary>

```bash
docker compose -f docker-compose.e2e.yaml up -d --wait --build

cd frontend
VITE_API_URL=http://localhost:8001 npm run build
VITE_API_URL=http://localhost:8001 npx vite preview --port 3000 --strictPort &
cd ..

cd e2e
npm ci
npx playwright install chromium
npx playwright test

npx playwright show-report

cd ..
docker compose -f docker-compose.e2e.yaml down -v
```

</details>

### Running a single spec

```bash
cd e2e
npx playwright test tests/student/student-home.spec.ts
```

### Running headed (visible browser)

```bash
cd e2e
npx playwright test --headed
```

## Test structure

```
e2e/
├── playwright.config.ts       # Playwright configuration
├── global-setup.ts            # Waits for backend + frontend to be healthy
├── fixtures/
│   ├── seed.ts                # Typed constants mirroring seed_dev.sql (IDs, emails)
│   ├── auth.fixture.ts        # Role-specific authenticated page fixtures
│   └── index.ts               # Barrel export
├── helpers/
│   ├── login.ts               # OTP login helper (uses fixed code 000000)
│   └── api.ts                 # Direct API calls for test setup / cleanup
└── tests/
    ├── public/                # Unauthenticated browsing (P-01 – P-03)
    ├── student/               # Student login, evaluation, results (S-01 – S-05)
    ├── lecturer/              # Lecturer home, evaluation, lock/unlock (L-01 – L-04)
    ├── admin/                 # User management, course management (A-01 – A-05)
    └── access-control/        # Role guards and redirects (AC-01 – AC-05)
```

## Test scenarios

| ID | Group | Scenario |
|----|-------|----------|
| P-01 | Public | Dashboard loads; course filter and search narrow the project list |
| P-02 | Public | Project detail is publicly accessible (title, tech stack, GitHub link) |
| P-03 | Public | Member email addresses are hidden from unauthenticated visitors |
| S-01 | Student | Full OTP login flow redirects to home and shows profile name |
| S-02 | Student | Student home shows only projects the user is a member of |
| S-03 | Student | Student submits a course evaluation (rating + peer feedback) |
| S-04 | Student | Results page shows locked state when `results_unlocked=false` |
| S-05 | Student | Results page shows scores and peer bonuses when unlocked |
| L-01 | Lecturer | Lecturer home shows assigned courses; create course modal opens |
| L-02 | Lecturer | Course projects page lists in-progress projects with evaluate links |
| L-03 | Lecturer | Lecturer saves draft evaluation, verifies persistence on reload, submits |
| L-04 | Lecturer | Admin unlocks then re-locks project results (two toggles; net state = seed) |
| A-01 | Admin | Admin creates a new student user; appears in user table |
| A-02 | Admin | Admin deactivates then reactivates a user (net state = active) |
| A-03 | Admin | Admin can access admin, lecturer, and public routes |
| AC-01 | Access | Unauthenticated users are redirected to `/login` for all protected routes |
| AC-02 | Access | Student is redirected from `/lecturer` and `/admin/users` |
| AC-03 | Access | Lecturer is redirected from `/admin/users` and `/student` |
| AC-04 | Access | Student cannot access another project's evaluation form (non-member) |
| AC-05 | Access | Authenticated student can still view public routes |

## OTP bypass

`E2E_OTP_OVERRIDE=000000` is set in `docker-compose.e2e.yaml`. This tells the backend to store `000000` as the OTP for every request instead of generating a random code. It is only active when `APP_ENV` is `e2e` or `local`; the backend validator raises at startup if it is set in any other environment.

## Database state guarantee

The tests do not perform any explicit cleanup. Because the entire `postgres-data-e2e` Docker volume is discarded on teardown (`docker compose down -v`), the database always starts fresh from `seed_dev.sql` on the next run.

## CI/CD integration

The workflow `.github/workflows/e2e.yml` runs automatically after `Backend Deployment (Dev)` or `Frontend Deployment (Dev)` completes on `main`. It uses concurrency group `e2e-main` with `cancel-in-progress: true`, so only one e2e run is active at a time.

The workflow can also be called directly by other workflows (e.g., a manual production deployment gate) via `workflow_call`.

## Future work — post-deploy smoke tests

> **TODO:** Add a `smoke-test.yml` workflow that runs after `Backend Deployment (Dev)` completes and hits the real dev Azure stack directly (no Docker Compose, no auth). 3–4 read-only tests: health endpoint, courses list, project detail. This validates that the deployed container is actually serving traffic without touching the dev database or requiring OTP bypass on the live environment.

---

## Design decisions

### Why Docker Compose instead of the shared dev environment

Running tests against the live `dev` Azure environment was considered and rejected for three reasons:

1. **OTP is the hard blocker.** The dev backend sends real OTPs via Azure Communication Services. There is no way to intercept the code in CI without either permanently deploying `E2E_OTP_OVERRIDE` to dev (which weakens the environment) or running a full SMTP interceptor inside Azure Container Apps (complex, fragile). The Docker Compose approach sidesteps this entirely.

2. **Shared state causes flaky tests.** Two concurrent CI runs (e.g. a backend push and a frontend push both triggering e2e) would race against the same dev database. An ephemeral container gives each run its own isolated database with no cross-run pollution.

3. **No Azure credentials needed.** The e2e CI job requires no OIDC, managed identity, or GitHub secrets scoped to Azure — the entire suite runs on the GitHub Actions runner.

The trade-off is that these tests do not exercise the real Azure deployment path (Container App networking, Static Web App routing, managed identity). That gap is addressed by the post-deploy smoke tests described below.

### Why the OTP override is safe

`E2E_OTP_OVERRIDE` is a setting in `backend/settings.py`. A `model_validator` raises `ValueError` at startup if the setting is non-null and `APP_ENV` is anything other than `local` or `e2e`. This makes it structurally impossible to enable on dev or production — misconfiguration fails loudly at boot rather than silently weakening auth.

### Why explicit test cleanup is not needed

The `postgres-data-e2e` Docker volume is discarded by `docker compose down -v` after every run. A fresh volume is created on the next `up`, migrations run from scratch, and `seed_dev.sql` is re-applied. The "no residual DB state" guarantee is enforced by infrastructure, not by test code.

The two tests that mutate existing seeded rows (L-03 inserts a new `project_evaluation`; S-03 inserts a new `course_evaluation`) are therefore free to write without any `afterAll` cleanup.
