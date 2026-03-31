from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from migration_settings import get_migration_settings

# Alembic Config object — provides access to values within the .ini file.
config = context.config

# Set up Python logging from the ini config file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from migration-specific settings.
# DATABASE_MIGRATION_URL must point to a role with full DDL+DML access.
config.set_main_option("sqlalchemy.url", get_migration_settings().database_migration_url)

# Wire SQLModel metadata for autogenerate support.
# Import all SQLModel table classes here once they exist so that Alembic can
# detect schema changes automatically (e.g. `alembic revision --autogenerate`).
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode.

    Offline mode generates plain SQL statements to stdout without opening a
    database connection (run via ``alembic upgrade head --sql``).  This is
    useful when a DBA needs to review and apply the SQL manually, or when a
    CI pipeline produces a migration-preview artifact without a live database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode.

    Online mode (the default) opens a real database connection and applies
    migrations directly.  This is the normal path for local development and
    for container startup scripts (e.g. ``alembic upgrade head``).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
