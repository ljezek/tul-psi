# GEMINI.md - Student Projects Catalogue (SPC)

This document provides a comprehensive overview of the Student Projects Catalogue project for AI assistants and developers.

## 🚀 Project Overview

The **Student Projects Catalogue (SPC)** is a centralized platform for the Faculty of Mechatronics, Informatics and Interdisciplinary Studies at the Technical University of Liberec (TUL). It serves as a repository for student projects and facilitates course and peer evaluations.

### Key Features
*   **Project Discovery:** Publicly searchable and filterable list of student projects.
*   **Role-Based Access:** Distinct views for Public, Student, and Lecturer roles.
*   **Evaluation System:** Multi-criteria project evaluations (Lecturers), course feedback (Students), and peer feedback (Students).
*   **OTP Authentication:** Secure, passwordless login restricted to `@tul.cz` email addresses.

### 🛠️ Tech Stack
*   **Backend:** Python 3.12, FastAPI, SQLModel (SQLAlchemy + Pydantic), PostgreSQL, Alembic.
*   **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, React Query.
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

### Best Practices
*   **Auth:** OTP tokens are single-use, 15-min expiry, @tul.cz only.
*   **Security:** JWT in HttpOnly/Secure cookies + XSRF protection (Double Submit Cookie).
*   **Observability:** All backend logs are structured JSON. Every request is traced via OpenTelemetry.
*   **Git Workflow:** All changes must be made via **Feature Branches** and **Pull Requests**. Never commit directly to `main`.
*   **Documentation:** Maintain `DESIGN.md` and `SPECIFICATION.md` as the source of truth for architecture and requirements.
