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

## Database roles

Two separate roles are created to follow the principle of least privilege:

| Role | Variable | Permissions | Used by |
|---|---|---|---|
| Admin | `POSTGRES_ADMIN_USER` (`tul_psi_admin`) | Full DDL + DML — can create/alter/drop tables and sequences | Alembic migrations, CI/CD |
| App | `POSTGRES_APP_USER` (`tul_psi_app`) | DML only — SELECT, INSERT, UPDATE, DELETE on tables; sequence usage | FastAPI application at runtime |

The admin role is created automatically by the PostgreSQL container.  
The app role is created by [`init-db.sh`](./init-db.sh), which runs once on the first container start.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `student_projects` | Database name |
| `POSTGRES_ADMIN_USER` | `tul_psi_admin` | Admin role name (full DDL+DML) |
| `POSTGRES_ADMIN_PASSWORD` | `tul_psi_admin` | Admin role password |
| `POSTGRES_PORT` | `5432` | Host port mapped to PostgreSQL |
| `POSTGRES_APP_USER` | `tul_psi_app` | Application role name (DML only) |
| `POSTGRES_APP_PASSWORD` | `tul_psi_app` | Application role password |
| `DATABASE_MIGRATION_URL` | see `.env.example` | SQLAlchemy URL for Alembic / CI/CD (admin role) |
| `DATABASE_URL` | see `.env.example` | SQLAlchemy URL for the FastAPI app (app role) |

> ⚠️ **Never commit `.env` or reuse these credentials outside local development.** Use your cloud provider's secrets management for staging and production environments.

## Useful commands

```bash
# Stop containers (data is preserved in the named volume)
docker compose down

# Stop containers and wipe all data
docker compose down -v

# Follow database logs
docker compose logs -f db

# Open a psql shell inside the running container (admin role)
docker compose exec db psql -U tul_psi_admin -d student_projects
```

## Notes

* Data is persisted in a named Docker volume (`postgres-data`). It survives container restarts but is removed when you run `docker compose down -v`.
* The container exposes a health check (`pg_isready`) so dependent services (e.g. the FastAPI backend) can wait until the database is ready before starting.
* DB schema and migrations are managed with **Alembic** — see [`docs/DESIGN.md`](../docs/DESIGN.md) for details.
