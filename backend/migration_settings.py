from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class MigrationSettings(BaseSettings):
    """Settings used exclusively by Alembic schema migrations.

    Kept separate from the main application ``Settings`` so that migration
    credentials (the privileged admin URL) do not leak into the app process.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Admin connection URL — full DDL+DML access.
    # Set DATABASE_ADMIN_URL in the environment or .env file.
    # Falls back to DATABASE_URL when DATABASE_ADMIN_URL is not set (e.g. in
    # environments that use a single DB user).
    database_admin_url: str | None = None
    database_url: str

    @property
    def migration_url(self) -> str:
        """Return the DB URL to use for Alembic schema migrations.

        Prefers DATABASE_ADMIN_URL (admin role with DDL+DML access) when set.
        Falls back to DATABASE_URL for environments that do not separate roles.
        """
        return self.database_admin_url or self.database_url


@lru_cache
def get_migration_settings() -> MigrationSettings:
    return MigrationSettings()
