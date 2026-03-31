# Backend — Student Projects Catalogue API

FastAPI backend service for the Student Projects Catalogue.

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — async web framework
- **[SQLModel](https://sqlmodel.tiangolo.com/)** — ORM built on SQLAlchemy + Pydantic
- **[Uvicorn](https://www.uvicorn.org/)** — ASGI server
- **[Ruff](https://docs.astral.sh/ruff/)** — fast Python linter & formatter
- **[pytest](https://pytest.org/)** — testing framework

## Local Development

All commands in this guide are run from the **`backend/` directory** unless noted otherwise.

### 1. Navigate to the backend folder

> Run from the **repository root**:

```bash
cd backend
```

### 2. Create and activate a virtual environment

**bash/zsh (macOS/Linux):**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**PowerShell (Windows):**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

> Run from **`backend/`**:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

> Run from **`backend/`**:

```bash
cp .env.example .env
```

Edit `.env` to match your local database settings (see `database/.env.example`).

### 5. Run the development server

Use `start.sh` to apply any pending database migrations and then start the server:

> Run from **`backend/`**:

```bash
./start.sh --reload
```

The `--reload` flag enables auto-reload (recommended during development).  
The script is equivalent to running these two commands manually:

```bash
alembic upgrade head
uvicorn main:app --reload
```

Any extra arguments passed to `start.sh` are forwarded directly to `uvicorn`.

The API will be available at <http://localhost:8000>.  
Interactive docs (Swagger UI) at <http://localhost:8000/docs>.

## Available Commands

All commands below are run from **`backend/`**.

| Command | Description |
|---------|-------------|
| `./start.sh --reload` | Apply migrations then start dev server with auto-reload |
| `uvicorn main:app --reload` | Start dev server without running migrations |
| `alembic upgrade head` | Apply all pending migrations (requires `DATABASE_MIGRATION_URL`) |
| `ruff check .` | Run linter |
| `ruff format --check .` | Check code formatting |
| `ruff format .` | Auto-format code |
| `pytest` | Run unit tests |
