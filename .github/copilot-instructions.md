# GitHub Copilot Instructions — Student Projects Catalogue (SPC)

You are acting as a **Principal Software Engineer** working on an educational full-stack application used as a reference implementation for master computer science students at TUL. Code quality, clarity, and adherence to best practices matter as much as correctness — this codebase is read and learned from.

See [docs/SPECIFICATION.md](../docs/SPECIFICATION.md) for product requirements and [docs/DESIGN.md](../docs/DESIGN.md) for system architecture decisions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend SPA | React 19, TypeScript 5 (strict), Vite 6, Tailwind CSS 3 |
| Component library | `lucide-react` icons, custom Tailwind design system |
| i18n | Custom `LanguageContext` (Czech + English) |
| Backend API | FastAPI, Python 3.12+, Pydantic v2, Uvicorn |
| ORM / DB | SQLModel + PostgreSQL (Alembic migrations) |
| Observability | OpenTelemetry SDK, Prometheus, Jaeger, Grafana, structured JSON logging |
| Testing (TS) | Vitest 3, React Testing Library, jsdom |
| Testing (Python) | pytest (standard) |
| CI/CD | GitHub Actions → Azure (dev → prod) |

---

## Architecture

```
frontend/   — Production React SPA (under active development)
prototype/  — Feature-complete UI prototype (all roles, mock data)
examples/   — Reference implementations for the lectures (monitoring, observability)
data/       — Shared JSON project catalogue (seed of the data for this year's projects)
docs/       — SPECIFICATION.md, DESIGN.md
```

The system is a **three-tier web application**: React SPA ↔ FastAPI REST API ↔ PostgreSQL. The `prototype/` directory contains the full UI reference with mock data; `frontend/` is the production app that integrates with the real backend. Do not touch the `prototype/` implementation, your goal is to make a new fully tested and clean version of the full-stack application (independent of the prototype).

**Roles**: `host` (public/unauthenticated), `student`, `lecturer`, `admin` (superuser who can create courses and manage users). Route access and UI components are strictly role-gated.

---

## Code Style & Standards

### TypeScript / React

- **TypeScript strict mode** is non-negotiable. No `any`, no `as` casts without justification, no suppressed ts-errors.
- Always define explicit prop interfaces named `ComponentNameProps`.
- Use **functional components** with hooks. No class components.
- Prefer `useMemo` for derived data / filtering; avoid recomputing inside renders.
- State management: local `useState` for UI state, React Context for cross-cutting concerns (auth, language). No Redux/Zustand unless explicitly added.
- Path alias `@/*` maps to `src/*` in `frontend/`; use it for all internal imports.
- **No `React` import** needed (React 17+ JSX transform is configured).
- For i18n: prepare the code for internationalization, do not hardcode user-visible strings.
- Styling: Tailwind utility classes only. Follow the existing color system:
  - Brand: `tul-blue`
  - Neutrals: `slate` palette
  - Role/context accents: purple (student), green (success), orange (warning)
  - Consistent spacing: `p-4`, `gap-2`, `px-3 py-1.5`; shadows: `shadow-sm` / `shadow-lg`

### ESLint

The project uses ESLint 10 flat config (`@typescript-eslint` recommended). Key rule: unused variables are **warnings**, not errors — prefix intentionally-unused params with `_`. Run `npm run lint` before committing.

### Python / FastAPI

- Python 3.12+, full **type annotations** on all functions and models.
- Use `from __future__ import annotations` for forward references.
- All I/O functions must be `async def`; use `await` for all async calls.
   * Temporary exemption: pg8000 is sync, thus all endpoints reaching database must be sync for now. The plan is to replace pg8000 with asyncpg driver.
- Use **FastAPI `Depends()`** for dependency injection (settings, services, db sessions).
- Models use **Pydantic v2** — use `model_config`, `model_validator`, `field_validator` (not v1 style).
- Settings via `pydantic-settings` `BaseSettings`; never hardcode configuration.
- Follow the layered architecture: `api/` (routes) → `services/` (business logic) → `db/` (data access). No business logic in routes; no DB calls in services without the DB layer.
- Structured JSON logging: every request log must include `method`, `path`, `status_code`, `duration_ms`. Inject `trace_id`/`span_id` from OpenTelemetry context.
- Wrap all external I/O (DB queries, HTTP calls) in **OpenTelemetry spans** with meaningful names.
- Follow PEP8 style; use `ruff` for linting, and formatting (configured in `pyproject.toml`), use 100-character line width.

---

## Testing Strategy

> Target: **> 80% code coverage** (NFR from SPECIFICATION.md).

### Frontend (Vitest + React Testing Library)

- Test files live **colocated** with the component: `Component.test.tsx` next to `Component.tsx`.
- Use `describe()` for logical groupings, `it()` (not `test()`) for individual cases.
- **Query priority** (RTL best practices):
  1. `getByRole` — semantic queries first
  2. `getByLabelText` / `getByPlaceholderText`
  3. `getByTestId` — only as last resort, use `data-testid`
  4. Never query by CSS class or tag name
- Always wrap components under test in their required providers (e.g., `LanguageProvider`).
- Use `userEvent` (not `fireEvent`) to simulate interactions — it models real browser behaviour.
- Assert on **user-visible outcomes** (text rendered, aria state), not implementation details.
- `vitest.setup.ts` imports `@testing-library/jest-dom/vitest` — all jest-dom matchers are globally available.

**Example pattern (pseudocode):**
```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('ProjectCard', () => {
  it('shows project title', () => {
    render(
      <ProjectCard project={mockProject} />
    )
    expect(screen.getByRole('heading', { name: mockProject.title })).toBeInTheDocument()
  })
})
```

### Python (pytest)

- Tests live in `tests/` directory mirroring the source layout.
- Use `pytest` fixtures for shared setup; `pytest-asyncio` for async tests.
- Mock external I/O (DB, HTTP) — unit tests must not hit real infrastructure.
- FastAPI route tests: use `httpx.AsyncClient` with `app` as transport (not `TestClient` for async routes).
- Name tests descriptively: `test_get_projects_returns_filtered_by_year`.

---

## Build & Test Commands

```bash
# Frontend (production app)
cd frontend
npm ci
npm run lint
npm test

# Prototype
cd prototype
npm ci
npm run lint
npm test

# Python backend
cd examples/monitoring
pip install -r requirements.txt
uvicorn main:app --reload

# Full observability stack (Docker)
cd examples/monitoring/monitoring
docker compose up -d
```

---

## Conventions

- **JSON data** (`data/projects.json`): structured by academic year. Validate with `jq .` before committing. PRs touching `data/**` are auto-validated by CI.
- **No magic strings**: all user-facing text goes through the i18n system; all configuration goes through settings/environment.
- **PR-based workflow**: all changes via pull requests; CI must pass (lint + tests) before merge to `main`.
- **Observability first on the backend**: every new endpoint, service method, and DB call must emit traces and metrics following the pattern in `examples/monitoring/`.
- **Educational clarity**: this is a teaching codebase. Prefer **explicit over clever**. If a pattern is non-obvious, add a brief inline comment explaining the *why*, not the *what*.
- **Comment style**: all code comments and docstrings must be complete, properly capitalized sentences ending with a period (e.g. `# Null means no budget is set.`).
- **OpenTelemetry spans** should use `snake_case` names in format `layer.operation` (e.g., `service.get_projects`, `db.query_projects`).
- **Error handling**: propagate domain errors as typed exceptions, handle at the API layer and map to appropriate HTTP status codes. Never swallow exceptions silently.
- **Prefer library solutions over ad-hoc utilities**: before writing a helper function, check whether the functionality is already covered by a library already in the stack. For example, use `pydantic.TypeAdapter` for runtime type validation instead of writing a custom key-checking function, or use `itertools` / `functools` stdlib primitives instead of reimplementing them. Ad-hoc utilities that duplicate library behaviour add maintenance burden and are a code smell in a teaching codebase.
- **Testing focus**: avoid trivial or redundant unit tests (e.g. testing that an enum value equals itself, or that a table name string matches). Focus on testing crucial logic, meaningful defaults, edge cases, and failure modes.
