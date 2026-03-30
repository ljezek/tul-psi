from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "student-projects-catalogue-backend"
    app_env: str = "local"

    # Application version — override via APP_VERSION env var (e.g. set by CI/CD pipeline).
    app_version: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
