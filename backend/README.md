# Backend — Student Projects Catalogue API

FastAPI backend service for the Student Projects Catalogue.

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — async web framework
- **[SQLModel](https://sqlmodel.tiangolo.com/)** — ORM built on SQLAlchemy + Pydantic
- **[Uvicorn](https://www.uvicorn.org/)** — ASGI server
- **[Ruff](https://docs.astral.sh/ruff/)** — fast Python linter & formatter
- **[pytest](https://pytest.org/)** — testing framework

## Local Development

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the development server

```bash
uvicorn main:app --reload
```

The API will be available at <http://localhost:8000>.  
Interactive docs (Swagger UI) at <http://localhost:8000/docs>.

## Available Commands

| Command | Description |
|---------|-------------|
| `uvicorn main:app --reload` | Start dev server with auto-reload |
| `ruff check .` | Run linter |
| `ruff format --check .` | Check code formatting |
| `ruff format .` | Auto-format code |
| `pytest` | Run unit tests |
