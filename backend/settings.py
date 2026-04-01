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

    # Secret used to sign and verify JWT session tokens.
    # Must be set to a long, random string in production — the default is only for local dev.
    jwt_secret: str = "dev-secret-CHANGE-ME-in-production"  # noqa: S105

    # When True, the plaintext OTP is printed to stderr after generation.
    # Enable only in non-production environments as a stand-in for SMTP delivery.
    show_otp_dev_only: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
