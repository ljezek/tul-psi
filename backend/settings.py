from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "student-projects-catalogue-backend"
    app_env: str = "local"
    # Full SQLAlchemy connection URL.  Set DATABASE_URL in the environment or
    # .env file.  See .env.example for the local-development value.
    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
