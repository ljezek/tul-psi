# Database

Local PostgreSQL instance for the **Student Projects Catalogue** backend.

## Roles & Configuration

The database configuration (roles, passwords, and initialization) is now managed via the root [`docker-compose.yaml`](../docker-compose.yaml).

| Role | Variable | Permissions | Used by |
|---|---|---|---|
| Admin | `POSTGRES_ADMIN_USER` | Full DDL + DML — can create/alter/drop tables and sequences | Alembic migrations, CI/CD |
| App | `POSTGRES_APP_USER` | DML only — SELECT, INSERT, UPDATE, DELETE on tables; sequence usage | FastAPI application at runtime |

The admin role is created automatically by the PostgreSQL container.  
The app role is created by [`init-db.sh`](./init-db.sh), which runs once on the first container start.

## Usage

Start the database as part of the full stack from the project root:

```bash
# Start everything
docker compose up -d

# Start only the database
docker compose up -d db
```

## Notes

* DB schema and migrations are managed with **Alembic** — see [`docs/DESIGN.md`](../docs/DESIGN.md) for details.
