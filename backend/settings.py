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

    # When True, the plaintext OTP is printed to stderr after generation.
    # Enable only in non-production environments as a stand-in for SMTP delivery.
    show_otp_dev_only: bool = False

    # Secret key used to sign JWT session cookies.
    # Must be a long, random string; override in production via environment variable.
    jwt_secret: str = "changeme-override-in-production"  # noqa: S105
    # HMAC-SHA256 is the recommended symmetric signing algorithm for JWTs.
    jwt_algorithm: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()
