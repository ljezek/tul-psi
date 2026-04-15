from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sentinel used as the default for jwt_secret so it can be detected at runtime.
# Must be at least 32 characters for HS256 algorithm.
_JWT_SECRET_PLACEHOLDER = "changeme-override-in-production!"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "student-projects-catalogue-backend"
    app_env: str = "local"

    # Application connection URL (DML only — no DDL / schema changes).
    # Used by the FastAPI application at runtime.
    database_url: str

    # Public base URL of the frontend SPA (e.g. https://spc.tul.cz in production).
    # Included in outgoing email bodies so recipients can navigate to the portal.
    frontend_url: str = "http://localhost:3000"

    # List of origins allowed to make cross-origin requests (CORS).
    # In production, this should be restricted to the actual frontend domain.
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Secret key used to sign JWT session cookies.
    # Must be a long, random string; override in production via the JWT_SECRET env var.
    jwt_secret: str = _JWT_SECRET_PLACEHOLDER
    # HMAC-SHA256 is the recommended symmetric signing algorithm for JWTs.
    jwt_algorithm: str = "HS256"

    # Support for Entra ID (Azure Managed Identity) for DB authentication.
    azure_managed_identity_enabled: bool = False

    @model_validator(mode="after")
    def _check_insecure_defaults_in_production(self) -> Settings:
        """Raise at startup when the JWT secret placeholder is used in production.

        This prevents a misconfigured deployment from silently accepting forged
        session cookies — all tokens would be forgeable with the well-known default.
        Override ``JWT_SECRET`` via the environment variable in non-local deployments.
        """
        if self.app_env == "production" and self.jwt_secret == _JWT_SECRET_PLACEHOLDER:
            raise ValueError(
                "JWT_SECRET must be overridden in production. "
                "Set the JWT_SECRET environment variable to a long, random string."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
