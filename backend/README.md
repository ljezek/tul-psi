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

### 4. Run the development server

> Run from **`backend/`**:

```bash
uvicorn main:app --reload
```

The API will be available at <http://localhost:8000>.  
Interactive docs (Swagger UI) at <http://localhost:8000/docs>.

## Available Commands

All commands below are run from **`backend/`**.

| Command | Description |
|---------|-------------|
| `uvicorn main:app --reload` | Start dev server with auto-reload |
| `ruff check .` | Run linter |
| `ruff format --check .` | Check code formatting |
| `ruff format .` | Auto-format code |
| `pytest` | Run unit tests |
