# Migrations

Schema migrations for the Student Projects Catalogue database, managed with [Alembic](https://alembic.sqlalchemy.org/).

## Usage

```bash
# Generate a new migration from model changes
alembic revision --autogenerate -m "<description>"

# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1
```

Migration files live in `versions/`. Every migration must include a working `downgrade()` function.
