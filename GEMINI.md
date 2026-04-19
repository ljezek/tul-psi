# GEMINI.md - Student Projects Catalogue (SPC)

This document provides a comprehensive overview of the Student Projects Catalogue project for AI assistants and developers.

## 🚀 Project Overview

The **Student Projects Catalogue (SPC)** is a centralized platform for the Faculty of Mechatronics, Informatics and Interdisciplinary Studies at the Technical University of Liberec (TUL). It serves as a repository for student projects and facilitates course and peer evaluations.

### Key Features
*   **Project Discovery:** Publicly searchable and filterable list of student projects.
*   **Course Discovery:** List of all courses with detailed syllabus and project links.
*   **Role-Based Access:** Distinct views for Public, Student, and Lecturer roles.
*   **Evaluation System:** Multi-criteria project evaluations (Lecturers), course feedback (Students), and peer feedback (Students).
*   **OTP Authentication:** Secure, passwordless login restricted to ``@tul.cz`` email addresses.

### 🛠️ Tech Stack
*   **Backend:** Python 3.12, FastAPI, SQLModel (SQLAlchemy + Pydantic), PostgreSQL, Alembic.
*   **Frontend:** React 19, TypeScript, Vite, Tailwind CSS. (Note: Migration to React Query is planned).
*   **Observability:** OpenTelemetry, Prometheus, Jaeger, Grafana (structured JSON logging).
*   **Infrastructure:** Docker (local), Azure (production), GitHub Actions (CI/CD).

## 📂 Directory Structure

*   `backend/`: FastAPI application, migrations, and tests.
*   `frontend/`: React Single Page Application (SPA).
*   `prototype/`: Initial React prototype for rapid design validation.
*   `database/`: Docker Compose configuration for local PostgreSQL.
*   `docs/`: Product Specification and Technical Design documents.
*   `examples/monitoring/`: Demonstration of monitoring and observability best practices.

## 💻 Getting Started

### 1. Database
Start the local PostgreSQL instance:
```bash
cd database
cp .env.example .env   # Configure as needed
docker compose up -d
```

### 2. Backend
Navigate to `backend/`, set up the environment, and start the server:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cp .env.example .env       # Configure DATABASE_URL
python seed.py             # Optional: seed dev data
./start.sh --reload        # Runs migrations and starts uvicorn
```
*   **API Docs:** `http://localhost:8000/docs`

### 3. Frontend
Navigate to `frontend/`, install dependencies, and start the dev server:
```bash
cd frontend
npm install
cp .env.example .env       # Set VITE_API_URL=http://localhost:8000
npm run dev                # Starts on http://localhost:3000
```

## 🧪 Development Conventions

### Linting & Formatting
*   **Backend:** Uses **Ruff**.
    *   `ruff check .` (Lint)
    *   `ruff format .` (Format)
*   **Frontend:** Uses **ESLint**.
    *   `npm run lint`

### Testing
*   **Backend:** uses **pytest** (Target: ≥ 80% coverage).
    *   `pytest`
*   **Frontend:** uses **Vitest** (Target: ≥ 80% coverage).
    *   `npm test`

### 💎 Best Practices

#### General
*   **Git Workflow:** All changes must be made via **Feature Branches** and **Pull Requests**. Never commit directly to `main`.
*   **Observability:** All backend logs are structured JSON. Every request is traced via OpenTelemetry.
*   **Tech Debt:** Document missing functionality or future improvements with `// TODO:` comments.

#### Frontend
*   **Internationalization (i18n):**
    *   Consistently use `t()` from `LanguageContext` for **all** user-visible strings.
    *   Maintain full support for both Czech (`cs`) and English (`en`).
    *   Add all new labels, filters, and error messages to `src/contexts/LanguageContext.tsx`.
*   **Testing:**
    *   Test non-trivial logic (e.g., client-side filtering, API parameter building).
    *   Colocate tests with components (`Component.test.tsx`).
    *   Priority: Query by role (`getByRole`) > Label (`getByLabelText`) > Test ID.
    *   Mock API responses carefully (handle lists/objects to avoid runtime errors during tests).
*   **State & Routing:**
    *   Persist UI state (like Dashboard filters) in the URL using `useSearchParams`. This ensures filters are remembered when navigating back.
    *   Use unique identifiers (integer IDs) for routing (e.g., `/courses/:id`) rather than names or codes.
*   **Accessibility (A11y):**
    *   Always provide `aria-label` for form inputs that don't have visible labels.
    *   Use semantic HTML elements (e.g., `<nav>`, `<main>`, `<section>`, `<h1>`-`<h6>`).
*   **Type Safety:**
    *   Maintain parity between backend schemas and frontend types (use `snake_case` matching the API).
    *   Avoid `any` types or `as` casts without a valid `// TODO:` justification.
*   **UI Components:**
    *   Be version-aware regarding libraries. For `lucide-react`, use available icons or logical fallbacks.
    *   **Icon Policy:** For the GitHub logo, always use the custom `<GitHubLogo />` component from `@/components/icons/GitHubLogo` to ensure brand consistency.
    *   **User Profile:** Profile editing is handled via a dedicated `/profile` route and a unified `<ProfileForm />` component. Always link to `/profile` for user settings.

#### Backend
*   **Quality Control:** BEFORE declaring backend changes ready for review, you MUST run `ruff format .`, `ruff check .`, and `pytest` from the `backend/` directory to ensure code quality and prevent regressions.
*   **Security:** JWT in HttpOnly/Secure cookies. Configure `CORSMiddleware` to strictly allow required origins (e.g., `localhost:3000`).
*   **Auth:** OTP tokens are single-use, 15-min expiry, `@tul.cz` only.
*   **API Design:** Ensure resources include necessary identifiers (IDs) for frontend routing.
