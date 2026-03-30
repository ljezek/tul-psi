# Database

Local PostgreSQL instance for the **Student Projects Catalogue** backend.

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (v2+)

## Quick start

```bash
# 1. Copy the example environment file (first time only)
cp .env.example .env

# 2. Start the database
docker compose up -d

# 3. Verify it is healthy
docker compose ps
```

The PostgreSQL server is now available at `localhost:5432` with the credentials defined in `.env`.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `student_projects` | Database name |
| `POSTGRES_USER` | `tul_psi` | Database user |
| `POSTGRES_PASSWORD` | `tul_psi` | Database password |
| `POSTGRES_PORT` | `5432` | Host port mapped to PostgreSQL |
| `DATABASE_URL` | see `.env.example` | SQLAlchemy connection string — will be consumed by the FastAPI backend once database integration is added |

> ⚠️ **Never commit `.env` or reuse these credentials outside local development.** Use your cloud provider's secrets management for staging and production environments.

## Useful commands

```bash
# Stop containers (data is preserved in the named volume)
docker compose down

# Stop containers and wipe all data
docker compose down -v

# Follow database logs
docker compose logs -f db

# Open a psql shell inside the running container
docker compose exec db psql -U tul_psi -d student_projects
```

## Notes

* Data is persisted in a named Docker volume (`postgres-data`). It survives container restarts but is removed when you run `docker compose down -v`.
* The container exposes a health check (`pg_isready`) so dependent services (e.g. the FastAPI backend) can wait until the database is ready before starting.
* DB schema and migrations are managed with **Alembic** — see [`docs/DESIGN.md`](../docs/DESIGN.md) for details.
