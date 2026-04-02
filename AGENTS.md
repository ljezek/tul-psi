# Agent Guidelines & Project Context

This document provides essential information for AI agents (Gemini CLI, Claude Code, etc.) and developers working on the **Student Projects Catalogue**.

For a deep dive into the engineering standards, architectural principles, and teaching-oriented coding style, see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## 🏗️ Project Structure

- **`backend/`**: Python 3.12+ FastAPI application.
- **`frontend/`**: React (TS) + Vite + Tailwind CSS SPA.
- **`prototype/`**: Initial React prototype for UI reference.
- **`docs/`**: Technical documentation (DESIGN.md, SPECIFICATION.md).
- **`database/`**: Docker Compose and initialization scripts for PostgreSQL.

---

## 🐍 Backend (Python / FastAPI)

- **Environment**: Use the virtual environment located at `backend/.venv`.
  - **Windows**: `. .venv\Scripts\Activate.ps1`
  - **Unix**: `source .venv/bin/activate`
- **Dependency Management**: `pyproject.toml` defines the project, but `requirements.txt` is also present.
- **Testing**:
  - Framework: `pytest` (with `pytest-asyncio`).
  - Run command: `python -m pytest` (from the `backend/` directory).
  - **Note**: SQLAlchemy async operations often require `greenlet`. For unit tests where a real DB is not needed, prefer mocking the session dependency to avoid `ValueError: the greenlet library is required`.
- **Code Style**:
  - **Ruff**: Used for both linting and formatting.
  - Lint: `ruff check .`
  - Format: `ruff format .`
- **Database Migrations**:
  - Tool: `alembic`.
  - Commands: `alembic upgrade head`, `alembic revision --autogenerate -m "description"`.
  - Migrations are stored in `backend/migrations/versions/`.

---

## ⚛️ Frontend (React / TypeScript)

- **Package Manager**: `npm`.
- **Commands**:
  - Development: `npm run dev`
  - Build: `npm run build`
  - Lint: `npm run lint` (ESLint)
- **Testing**: `vitest` + React Testing Library.
  - Run command: `npm test`

---

## 🛡️ Security & Authentication

- **OTP Flow**: The system uses a 6-digit One-Time Password sent via email.
- **Domain Restriction**: Only `@tul.cz` email addresses are allowed for registration/login.
- **Authorization**: Role-based access control (`ADMIN`, `LECTURER`, `STUDENT`).
- **Session**: Handled via HttpOnly Secure cookies (JWT).

---

## 🤖 AI Interaction Mandates

1. **Surgical Edits**: Prefer using targeted `replace` or `patch` tools over rewriting entire files.
2. **Test First**: When fixing bugs, create a reproduction test case first.
3. **Validation**: Always run the relevant test suite (`pytest` or `vitest`) after making code changes.
4. **Style Consistency**: Adhere strictly to the `ruff` (Python) and `eslint` (TS) configurations.
5. **Documentation**: Keep `docs/DESIGN.md` in sync with API or Schema changes.
6. **Migrations**: When modifying models in `backend/models/`, always check if a database migration is required.
