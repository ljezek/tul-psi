from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
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
# Importing the table classes registers them with SQLModel.metadata so that
# `alembic revision --autogenerate` can detect schema changes automatically.
import models  # noqa: F401, E402

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


def do_run_migrations(connection: Connection) -> None:
    """Execute pending migrations against an already-open synchronous connection.

    This helper is passed to ``connection.run_sync()`` so that the synchronous
    Alembic migration context can be driven from an async connection.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in online mode using an async connection.

    Online mode (the default) opens a real database connection and applies
    migrations directly.  The async engine keeps the migration driver
    (asyncpg) consistent with the application driver so that a separate
    sync driver is not required.
    """
    migration_settings = get_migration_settings()
    engine_kwargs = {
        "poolclass": NullPool,
    }

    if migration_settings.azure_managed_identity_enabled:
        from db.token_provider import TokenProvider

        token_provider = TokenProvider()
        engine_kwargs["connect_args"] = {
            "password": token_provider.get_token,
            "ssl": True,
        }

    connectable = create_async_engine(
        migration_settings.database_migration_url,
        **engine_kwargs,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
