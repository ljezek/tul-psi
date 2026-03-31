from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "student-projects-catalogue-backend"
    app_env: str = "local"

    # Application connection URL (DML only — no DDL / schema changes).
    # Used by the FastAPI application at runtime.
    database_url: str

    # Admin connection URL (full DDL+DML access).
    # When set, Alembic uses this URL for schema migrations so that the admin
    # role (not the app role) performs schema changes.  Falls back to
    # database_url when not provided (e.g. in environments that use a single
    # DB user).
    database_admin_url: str | None = None

    @property
    def migration_url(self) -> str:
        """Return the DB URL to use for Alembic schema migrations.

        Prefers DATABASE_ADMIN_URL when set so that migrations run under the
        privileged admin role.  Falls back to DATABASE_URL for environments
        that do not separate roles.
        """
        return self.database_admin_url or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
