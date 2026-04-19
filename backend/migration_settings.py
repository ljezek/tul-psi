from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class MigrationSettings(BaseSettings):
    """Settings used exclusively by Alembic schema migrations.

    Kept separate from the main application ``Settings`` so that migration
    credentials (the privileged admin URL) do not leak into the app process.
    Set DATABASE_MIGRATION_URL to the admin connection URL (full DDL+DML access).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Migration connection URL — full DDL+DML access.
    # Set DATABASE_MIGRATION_URL in the environment or .env file.
    # Typically points to the admin role; can be set to the same value as
    # DATABASE_URL in environments that use a single DB user.
    database_migration_url: str

    # Support for Entra ID (Azure Managed Identity) for DB authentication.
    azure_managed_identity_enabled: bool = False
    azure_client_id: str | None = None


@lru_cache
def get_migration_settings() -> MigrationSettings:
    return MigrationSettings()
