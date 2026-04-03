# Design Doc

This document presents the technical plan for implementing the Student Projects Catalogue project. For a high-level overview see [/README.md](../README.md); for business requirements see [SPECIFICATION.md](./SPECIFICATION.md).

## System Architecture Overview

The following diagram depicts the layout of the project components and core technologies:

```mermaid
flowchart TD
  UI[Frontend - React SPA]
  API[Backend - Python / FastAPI]
  DB[(Database - PostgreSQL)]

  UI -- HTTPS/JSON --> API
  API -- SQLModel --> DB
```

* **Frontend** (React Single Page Application):
   * Vite and Tailwind CSS
   * `ProjectDashboard`: Displays the list of all student projects.
   * `ProjectDetails`: View for specific project info, including links to GitHub and live app.
   * `EvaluationModule`: Forms for Student Course Evaluation, Lecturer Project Evaluation, and Student Peer Feedback.
   * `State Management` (React Query): Handles data fetching and caching.
* **Backend** (Python / FastAPI):
   * `Auth Middleware`: Validation of authentication state (validates JWT).
   * `Course Service`: Logic for CRUD operations on courses (including academic terms and project configuration).
   * `Project Service`: Logic for CRUD operations on projects, including student invite flow.
   * `Evaluation Service`: Business logic for lecturer evaluations (per-criteria scoring) and peer review.
   * `Persistence Layer`: Interface for database communication (using SQLModel)
* **Database** (PostgreSQL)
* **Infrastructure**
   * Monitoring: Storage for monitoring data and logs.
   * Testing: pytest for unit and integration tests; Playwright for UI tests.
   * Deployment: Azure Cloud, GitHub Actions (CI/CD)
   * Local development: Docker

## Data Model

### Entity Relationships

```mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string github_alias
        string name
        string role "ADMIN | LECTURER | STUDENT"
        bool is_active
        timestamp created_at
    }
    OTP_TOKEN {
        int id PK
        int user_id FK
        string token_hash
        int attempts "failed verify attempts"
        timestamp expires_at
        bool used
        timestamp created_at
    }
    COURSE {
        int id PK
        string code UK
        string name
        text syllabus
        string term "SUMMER | WINTER"
        string project_type "TEAM | INDIVIDUAL"
        int min_score "minimum score to pass"
        int peer_bonus_budget "null = no bonus points"
        json evaluation_criteria
        json links
        int created_by FK
        timestamp created_at
    }
    PROJECT {
        int id PK
        string title
        text description
        string github_url
        string live_url
        json technologies
        bool results_unlocked
        int course_id FK
        int academic_year "e.g. 2025"
        timestamp created_at
    }
    PROJECT_MEMBER {
        int id PK
        int project_id FK
        int user_id FK
        int invited_by FK
        timestamp invited_at
        timestamp joined_at
    }
    PROJECT_EVALUATION {
        int id PK
        int project_id FK
        int lecturer_id FK
        json scores
        bool submitted        
        timestamp submitted_at
    }
    COURSE_EVALUATION {
        int id PK
        int project_id FK
        int student_id FK
        int rating "1-5"
        text strengths
        text improvements
        bool submitted
        timestamp updated_at
    }
    PEER_FEEDBACK {
        int id PK
        int course_evaluation_id FK
        int receiving_student_id FK
        text strengths
        text improvements
        int bonus_points
    }

    COURSE_LECTURER {
        int course_id FK
        int user_id FK
        timestamp assigned_at
    }

    COURSE_LECTURER }|--|| COURSE : "course"
    COURSE_LECTURER }|--|| USER : "lecturer"
    USER ||--o{ OTP_TOKEN : "authenticates"
    USER ||--o{ COURSE : "created_by"
    COURSE ||--o{ PROJECT : "contains"
    PROJECT ||--o{ PROJECT_MEMBER : "members"
    USER ||--o{ PROJECT_MEMBER : "is_member"
    USER ||--o{ PROJECT_MEMBER : "invited_by"
    PROJECT ||--o{ PROJECT_EVALUATION : "receives"
    USER ||--o{ PROJECT_EVALUATION : "submits"
    PROJECT ||--o{ COURSE_EVALUATION : "receives"
    USER ||--o{ COURSE_EVALUATION : "submits"
    COURSE_EVALUATION ||--o{ PEER_FEEDBACK : "includes"
    USER ||--o{ PEER_FEEDBACK : "receiving"
```

### JSONB Column Formats

**`COURSE.evaluation_criteria`** — configured once per course by ADMIN. `code` is a short immutable identifier used as the foreign key in `PROJECT_EVALUATION.scores`; `description` is the student-facing label:

```json
[{ "code": "code_quality",  "description": "Code Quality & Architecture", "max_score": 25 },
 { "code": "documentation", "description": "Documentation & README",       "max_score": 20 },
 { "code": "presentation",  "description": "Final Presentation",           "max_score": 15 }]
```

**`COURSE.links`** — arbitrary list of labelled URLs:

```json
[{ "label": "eLearning",       "url": "https://elearning.tul.cz/..." },
 { "label": "STAG",            "url": "https://stag.tul.cz/..." },
 { "label": "Study Materials", "url": "https://..." }]
```

**`PROJECT_EVALUATION.scores`** — one entry per criterion per lecturer. Each assigned lecturer submits their own `PROJECT_EVALUATION` row; `(project_id, lecturer_id)` is unique. Scores are averaged across all lecturers when computing a student's final result:

```json
[{ "criterion_code": "code_quality", "score": 22,
   "strengths": "Well-structured codebase",
   "improvements": "Add docstrings to the service layer" }]
```

**`PROJECT.technologies`** — flat string array:

```json
["Python", "FastAPI", "React", "PostgreSQL"]
```

### Database Migrations

Schema changes are managed with **Alembic** (the standard migration tool for SQLModel/SQLAlchemy).

| Command | Purpose |
|---|---|
| `alembic revision --autogenerate -m "<description>"` | Generate a migration file from model diff |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back the last migration |

* Migration files live in `migrations/versions/`.
* Every migration **must** include a working `downgrade()` function.
* Migrations are applied automatically on container startup via the `docker-compose.yml` entrypoint.

## Interaction Design

### OTP Authentication Flow

See [Security Architecture](#security-architecture) for the full sequence diagram.

### Student Evaluation Processing

The following sequence covers a student opening and submitting the **Course & Peer Evaluation Form** in the Student Zone.

```mermaid
sequenceDiagram
    actor Student
    participant Frontend
    participant API
    participant DB as PostgreSQL

    Student->>Frontend: Open Student Zone → Evaluation tab
    Frontend->>API: GET /api/v1/projects/{id}/course-evaluation
    API->>DB: Fetch project, course config (project_type, peer_bonus_budget), teammates
    DB-->>API: Project data + draft (if any) + submitted flag
    API-->>Frontend: {project, teammates, draft, submitted}

    alt submitted (evaluation already saved)
        Frontend-->>Student: Show saved evaluation (read-only)
    else draft or not yet started
        Frontend-->>Student: Render editable form (course section + per-teammate sections)
        Note over Frontend,Student: Student can save a draft and return to edit at any time before publishing
        Student->>Frontend: Fill course rating (1–5), strengths, improvements
        Student->>Frontend: Fill per-teammate: strengths, improvements, bonus_points
        Student->>Frontend: Click Publish
        Frontend->>API: PUT /api/v1/projects/{id}/course-evaluation {submitted: true, ...}
        API->>DB: Validate: student is member AND has not yet submitted
        alt validation fails
            API-->>Frontend: 422 / 409
            Frontend-->>Student: Show error
        else validation passes
            API->>DB: UPSERT course_evaluation + peer_feedback rows (submitted = true)
            API->>DB: Count submitted evaluations vs total project members
            alt all members submitted AND all assigned lecturers have submitted project_evaluation
                API->>DB: SET project.results_unlocked = true
            end
            API-->>Frontend: 200 OK
            Frontend-->>Student: Evaluation submitted successfully
        end
    end
```

Results become visible to each student once **both** conditions are met: **all** assigned lecturers have submitted a project evaluation **and** every team member has submitted their course evaluation. Any assigned lecturer can also trigger an early unlock via `POST /projects/{id}/unlock` to unblock results in cases where a student is absent or a lecturer cannot submit (preventing a deadlock). Peer feedback sections are only included in the form for **TEAM** projects; `peer_bonus_budget` on the course controls whether bonus-point distribution is shown (null = disabled).

**Peer bonus semantics:** `peer_bonus_budget` is a *per-teammate* budget. In a team of *N* students, each student distributes a total of `(N − 1) × peer_bonus_budget` points across their teammates. Each individual teammate may receive anywhere from 0 to `2 × peer_bonus_budget` points. The final peer bonus score for a student is the **average** of the bonus points they received from each teammate. A student passes if their final score (sum of average lecturer criterion scores + average received peer bonus points) meets `COURSE.min_score`.

## API & Interface Specification

All endpoints are prefixed with `/api/v1`. Authenticated routes rely on an **HttpOnly session cookie** set by the server (see [Security Architecture](#security-architecture)); no `Authorization` header is needed. State-changing requests must also include the `X-XSRF-Token` header (Double Submit Cookie pattern). Required roles are noted inline.

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/otp/request` | – | Request a one-time code |
| `POST` | `/auth/otp/verify` | – | Exchange OTP for JWT |
| `POST` | `/auth/logout` | – | Expire the session cookie |

```json
// POST /auth/otp/request — request body
{ "email": "jan.novak@tul.cz" }
// 200 → { "message": "If this email is registered, an OTP has been sent." }
// Note: always returns 200 regardless of whether the email exists to prevent user enumeration.

// POST /auth/otp/verify — request body
{ "email": "jan.novak@tul.cz", "otp": "483921" }
// 200 + Set-Cookie: session=<jwt>; HttpOnly; Secure; SameSite=Strict
// 200 → {} · 401 → { "detail": "Invalid or expired code" } · 429 → { "detail": "Too many attempts — request a new code" }

// POST /auth/logout — no request body
// 200 → {} + Set-Cookie: session=; Max-Age=0; HttpOnly; Secure; SameSite=Strict
// Idempotent — safe to call without an active session.
```

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | – | Liveness / readiness check |

```json
// 200 → { "status": "ok", "version": "1.0.0" }
```

### Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/users` | ADMIN | List all users |
| `POST` | `/users` | ADMIN | Create a user |
| `GET` | `/users/me` | ANY | Get current user's profile |
| `PATCH` | `/users/me` | ANY | Update current user's name or GitHub alias |
| `GET` | `/users/{id}` | ADMIN | Get user by ID |
| `PATCH` | `/users/{id}` | ADMIN | Update name or role |

```json
// User schema
{ "id": 1, "email": "jan.novak@tul.cz", "github_alias": "jnovak", "name": "Jan Novák", "role": "STUDENT", "is_active": true }
```

### Courses

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/courses` | – | List all courses |
| `POST` | `/courses` | ADMIN | Create a course |
| `GET` | `/courses/{id}` | – | Get course details |
| `PATCH` | `/courses/{id}` | ADMIN, LECTURER | Update course |
| `POST` | `/courses/{id}/lecturers` | ADMIN, LECTURER | Assign a lecturer |
| `DELETE` | `/courses/{id}/lecturers/{user_id}` | ADMIN, LECTURER | Remove a lecturer |
| `POST` | `/courses/{id}/projects` | ADMIN, LECTURER | Seed a project (assigns course & year; sends invite email to owner) |
| `GET` | `/courses/{id}/evaluation-overview` | LECTURER | Aggregated project scores and peer feedback; filter with `?year=2025` |

```json
// Course schema
{
  "id": 1, "code": "PSI", "name": "Projektový seminář informatiky",
  "syllabus": "...", "term": "WINTER", "project_type": "TEAM",
  "peer_bonus_budget": 10,
  "min_score": 50,
  "evaluation_criteria": [{ "code": "code_quality", "description": "Code Quality & Architecture", "max_score": 25 }],
  "links": [{ "label": "eLearning", "url": "https://..." }, { "label": "STAG", "url": "https://..." }]
}

// POST /courses/{id}/projects — request body
{ "title": "Student Projects Catalogue", "academic_year": 2025, "owner_email": "jan.novak@tul.cz" }
```

### Projects

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/projects` | – | List projects; query: `q`, `course`, `year`, `term`, `technology`, `student` |
| `GET` | `/projects/{id}` | – | Get project detail |
| `PATCH` | `/projects/{id}` | STUDENT (member), LECTURER | Update title, description, URLs, technologies |
| `POST` | `/projects/{id}/members` | STUDENT (member), LECTURER | Add member by email (creates user if needed; sends notification email with login link) |

```json
// Project schema
{
  "id": 1, "title": "Student Projects Catalogue",
  "description": "...", "github_url": "https://github.com/...", "live_url": "https://...",
  "technologies": ["Python", "FastAPI", "React"],
  "academic_year": 2025,
  "course": { "id": 1, "code": "PSI", "name": "Projektový seminář informatiky", "term": "WINTER" },
  "members": [{ "id": 5, "github_alias": "jnovak", "name": "Jan Novák" }]
}
```

### Evaluations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/projects/{id}/course-evaluation` | STUDENT (member) | Get form data: teammates, course config, current draft, submitted status |
| `PUT` | `/projects/{id}/course-evaluation` | STUDENT (member) | Save draft or publish course evaluation & peer feedback |
| `GET` | `/projects/{id}/project-evaluation` | LECTURER | Get submitted project evaluation |
| `POST` | `/projects/{id}/project-evaluation` | LECTURER | Submit project evaluation |
| `POST` | `/projects/{id}/unlock` | LECTURER | Manually unlock results (overrides automatic unlock condition) |
| `GET` | `/projects/{id}/results` | STUDENT (member) | View received results (only when `results_unlocked = true`) |

```json
// PUT /projects/{id}/course-evaluation — request body
// Set submitted=false to save a draft; true to lock and publish
{
  "submitted": true,
  "rating": 4,
  "strengths": "...",
  "improvements": "...",
  "peer_evaluations": [
    { "receiving_student_id": 7, "strengths": "...", "improvements": "...", "bonus_points": 2 }
  ]
}

// POST /projects/{id}/project-evaluation — request body (LECTURER)
// Each assigned lecturer submits independently; (project_id, lecturer_id) is unique.
{
  "scores": [
    { "criterion_code": "code_quality", "score": 22,
      "strengths": "Well-structured codebase", "improvements": "Add docstrings" }
  ]
}
```

## Infrastructure & Deployment

> [!NOTE]
> TODO(ljezek): Populate this once we move to the start of final milestone - Cloud deployment.

Azure cloud environment setup, resource selection, and the CI/CD pipeline architecture

High-level plan:

```mermaid
flowchart LR
    FB[Feature Branch]
    PR[Pull Request]
    MAIN[Main Branch]
    DEV[DEV environment]
    PROD[PROD environment]

    FB -- Unit Test & Code Style --> PR
    PR -- Code Review --> MAIN
    MAIN -- Build & Test --> DEV
    DEV -- Integration Tests --> PROD
```

## Reliability & Observability

### Local Observability Stack

The local development environment ships a pre-wired observability stack (see `examples/monitoring/monitoring/docker-compose.yml`) composed of four containers:

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| `otel-collector` | `otel/opentelemetry-collector-contrib` | 4317 (gRPC), 4318 (HTTP) | Central OTLP receiver; fans out to Jaeger and Prometheus |
| `jaeger` | `jaegertracing/all-in-one` | 16686 | Distributed trace viewer |
| `prometheus` | `prom/prometheus` | 9090 | Metrics storage (remote-write receiver enabled) |
| `grafana` | `grafana/grafana` | 3001 | Dashboards; auto-provisioned data sources and an overview dashboard (port 3001 avoids conflict with the React dev server on :3000) |

```mermaid
flowchart LR
    FE[React Frontend] -- "otel-js-sdk HTTP :4318" --> OC
    App[FastAPI Backend] -- "OTLP HTTP :4318" --> OC[OTel Collector]
    OC -- "OTLP gRPC" --> J[Jaeger :16686]
    OC -- "Remote Write" --> P[Prometheus :9090]
    P -- datasource --> G[Grafana :3001]
    J -- datasource --> G
```

### Instrumentation

Both the backend and the React frontend emit telemetry signals via the OpenTelemetry SDK.

**Backend** (Python `opentelemetry-sdk`):

**Traces** — every inbound request creates a span. Trace context is propagated to outbound HTTP calls and DB queries, enabling end-to-end trace views in Jaeger.

**Metrics** — emitted with OTLP and stored in Prometheus:

| Metric | Type | Description |
|--------|------|-------------|
| `http_server_requests_total` | Counter | Total inbound HTTP requests |
| `http_server_request_duration` (ms) | Histogram | Inbound request latency |
| `http_client_requests_total` | Counter | Outbound HTTP calls |
| `http_client_request_duration` (ms) | Histogram | Outbound call latency |
| `db_queries_total` | Counter | Total DB query calls |
| `db_query_duration` (ms) | Histogram | DB query latency |

**Logs** — structured JSON emitted to stdout via `python-json-logger`. Each record includes `trace_id` and `span_id` fields for correlation with Jaeger traces.

**Frontend** (`@opentelemetry/sdk-web`):

RUM traces (page loads, route transitions, and `fetch`/`xhr` call spans) are sent directly from the React app to the OTel Collector at `:4318` via OTLP/HTTP. This enables full end-to-end traces from user interaction through the API to the database, visible in Jaeger.

### SLI / SLO Targets

| SLI | Target |
|-----|--------|
| API availability | ≥ 99.5 % over a rolling 30-day window |
| P95 request latency (`GET /api/v1/projects`) | < 300 ms |
| 5xx error rate | < 0.5 % |

Alert thresholds are configured in Grafana and stored in `examples/monitoring/monitoring/grafana/provisioning/`.

## Security Architecture

### OTP Login Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant API
    participant DB as PostgreSQL
    participant SMTP as Email (SMTP)

    User->>Frontend: Enter @tul.cz email address
    Frontend->>API: POST /api/v1/auth/otp/request {email}
    API->>API: Reject if domain ≠ tul.cz → 422 Unprocessable Entity
    API->>DB: SELECT user WHERE email = ?
    alt user not found
        API-->>Frontend: 200 OK (same response as found)
        Note over API: Silent success prevents user enumeration
    else user found
        API->>API: Generate random 6-digit OTP
        API->>API: token_hash = bcrypt(otp, salt)
        API->>DB: INSERT otp_tokens (user_id, token_hash, attempts=0, expires_at = now + 15 min)
        API->>SMTP: Send OTP email
        API-->>Frontend: 200 OK
        Frontend-->>User: Check your email for a one-time code
        User->>Frontend: Enter 6-digit OTP
        Frontend->>API: POST /api/v1/auth/otp/verify {email, otp}
        API->>DB: SELECT token JOIN user WHERE user.email=? AND used=false AND expires_at > now()
        alt not found or expired
            API-->>Frontend: 401 Unauthorized
            Frontend-->>User: Invalid or expired code
        else token found
            API->>DB: INCREMENT otp_tokens SET attempts = attempts + 1
            alt attempts > 5
                API->>DB: SET used = true (invalidate token)
                API-->>Frontend: 429 Too Many Requests
                Frontend-->>User: Too many attempts — request a new code
            else within attempt limit
                API->>API: bcrypt.checkpw(otp, token_hash)
                alt hash mismatch
                    API-->>Frontend: 401 Unauthorized
                    Frontend-->>User: Invalid or expired code
                else hash matches
                    API->>DB: UPDATE otp_tokens SET used = true
                    API->>API: Sign JWT {user_id, role, exp: now + 8 h}
                    API-->>Frontend: 200 + Set-Cookie: session=<jwt>; HttpOnly; Secure; SameSite=Strict
                    Frontend-->>User: Redirect to role-based route
                end
            end
        end
    end
```

> [!NOTE]
> `/auth/otp/request` returns `200 OK` regardless of whether the email is registered. Returning `404` for unknown addresses would allow an attacker to enumerate valid user accounts (user enumeration attack). The user sees the same "check your email" message either way; unregistered addresses simply receive no email.

OTP tokens are **single-use**, expire after **15 minutes**, and are invalidated after **5 failed verification attempts**. Only `@tul.cz` email addresses are accepted — the API returns `422 Unprocessable Entity` for any other domain. The OTP is hashed with **bcrypt** (per-token salt) before storage; plain SHA-256 would be trivially reversible offline against a 6-digit space. The plaintext OTP is never stored.

### Additional Security Controls

* **Session cookie** — on successful OTP verification the server sets `Set-Cookie: session=<jwt>; HttpOnly; Secure; SameSite=Strict`. The JWT is never exposed to JavaScript, eliminating token exfiltration via XSS.
* **CSRF/XSRF** — because the JWT lives in a cookie, state-changing requests must include an `X-XSRF-Token` header following the **Double Submit Cookie** pattern; the backend validates that the header value matches the XSRF cookie.
* **CORS** — strict allowlist of trusted frontend origins configured on the FastAPI app.

## Testing Strategy

### Unit Tests

**Backend** — pytest with `pytest-cov`:

* Tests cover the service layer and API route handlers; the persistence layer is replaced with in-memory fakes (the pattern from `examples/monitoring/db/fake_db.py`).
* Coverage target: **≥ 80 %** line coverage, enforced in CI with `--cov-fail-under=80`.
* Run locally: `pytest --cov=app --cov-report=term-missing`

**Frontend** — Vitest + React Testing Library:

* Component-level tests (see `frontend/src/App.test.tsx` as the baseline).
* The API layer is mocked via MSW (Mock Service Worker) — no real network calls.
* Coverage target: **≥ 80 %** branch coverage.
* Run locally: `npm run test`

### Integration / UI Tests (Playwright)

End-to-end tests exercise complete user journeys against a running local Docker environment:

| Test Suite | Key Scenarios Covered |
|---|---|
| `public_discovery` | Filter projects by course / technology / name; open project detail |
| `otp_auth` | Request OTP, enter code, verify redirect to correct role route |
| `student_zone` | Login via invite email link; edit project details; submit course evaluation & peer feedback |
| `lecturer_panel` | Seed a project for a course and year; submit lecturer evaluation |
| `evaluation_unlock` | Results become visible to student after all conditions are met |

Tests run against the Docker Compose stack with a dedicated test database that is wiped and re-seeded from fixtures before each suite.

### CI/CD Quality Gates

| Stage | Checks |
|---|---|
| PR (every push) | Ruff (Python lint + format), ESLint, `pytest` with coverage gate, `vitest` |
| Merge to `main` | All PR checks + Playwright integration tests |
| Deploy to DEV / PROD | _(Azure — milestone 3)_ |
