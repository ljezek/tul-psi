from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sentinel used as the default for jwt_secret so it can be detected at runtime.
# Must be at least 32 characters for HS256 algorithm.
_JWT_SECRET_PLACEHOLDER = "changeme-override-in-production!"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "student-projects-catalogue-backend"
    app_env: str = "local"
    app_version: str = "0.0.0-local"

    # Application connection URL (DML only — no DDL / schema changes).
    # Used by the FastAPI application at runtime.
    database_url: str | None = None

    # Migration connection URL (DDL — high privilege).
    # Used only by the Alembic migration job.
    database_migration_url: str | None = None

    # Public base URL of the frontend SPA (e.g. https://spc.tul.cz in production).
    # Included in outgoing email bodies so recipients can navigate to the portal.
    frontend_url: str = "http://localhost:3000"

    # List of origins allowed to make cross-origin requests (CORS).
    # In production, this should be restricted to the actual frontend domain.
    allowed_origins: list[str] | str = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Regex of origins allowed to make cross-origin requests (CORS).
    # Useful for dynamic SWA preview URLs in dev.
    allowed_origin_regex: str | None = None

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Support comma-separated strings or JSON lists for CORS origins."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    result = json.loads(v)
                    if isinstance(result, list):
                        return result
                except (json.JSONDecodeError, TypeError):
                    pass
            # Handle empty string or comma-separated string
            if not v:
                return []
            return [i.strip() for i in v.split(",") if i.strip()]
        return v if isinstance(v, list) else [v]

    # Secret key used to sign JWT session cookies.
    # Must be a long, random string; override in production via the JWT_SECRET env var.
    jwt_secret: str = _JWT_SECRET_PLACEHOLDER
    # HMAC-SHA256 is the recommended symmetric signing algorithm for JWTs.
    jwt_algorithm: str = "HS256"

    # Support for Entra ID (Azure Managed Identity) for DB authentication.
    azure_managed_identity_enabled: bool = False
    azure_client_id: str | None = None

    # Azure Communication Services — used for email delivery in non-local environments.
    # ACS_CONNECTION_STRING is injected from an ACA secret (set via Bicep / Key Vault).
    # ACS_FROM_ADDRESS is the verified sender address provisioned by the ACS managed domain.
    acs_connection_string: str | None = None
    acs_from_address: str | None = None

    # Health check URL for the OTel collector sidecar/service.
    # In Azure, it's typically http://localhost:13133.
    # In local Docker Compose, it's http://otel-collector:13133.
    otel_collector_health_url: str = "http://localhost:13133"

    # When set, all OTP tokens use this fixed code instead of a random one.
    # Must be unset (None) in dev & production — enforced by the validator below.
    e2e_otp_override: str | None = None

    @model_validator(mode="after")
    def _validate_settings(self) -> Settings:
        """Validate critical configuration after loading from environment."""
        # 1. Ensure at least one database connection URL is provided.
        if not self.database_url and not self.database_migration_url:
            raise ValueError(
                "At least one of DATABASE_URL or DATABASE_MIGRATION_URL must be provided."
            )

        # 2. Raise at startup when the JWT secret placeholder is used in production.
        if self.app_env not in ("local", "e2e") and self.jwt_secret == _JWT_SECRET_PLACEHOLDER:
            raise ValueError(
                f"JWT_SECRET must be overridden in the '{self.app_env}' environment. "
                "Set the JWT_SECRET environment variable to a long, random string."
            )

        # 3. Prevent the OTP override from being active outside of safe environments.
        if self.e2e_otp_override and self.app_env not in ("local", "e2e"):
            raise ValueError(
                "e2e_otp_override must not be set outside of 'local' or 'e2e' environments."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
