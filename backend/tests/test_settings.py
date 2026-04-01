from __future__ import annotations

import pytest

from settings import _JWT_SECRET_PLACEHOLDER, Settings


def test_settings_raises_in_production_with_placeholder_jwt_secret() -> None:
    """Settings must refuse to start in production when jwt_secret is still the placeholder."""
    with pytest.raises(ValueError, match="JWT_SECRET must be overridden in production"):
        Settings(
            database_url="postgresql+asyncpg://x:x@localhost/x",
            app_env="production",
            jwt_secret=_JWT_SECRET_PLACEHOLDER,
        )


def test_settings_allows_placeholder_jwt_secret_in_local_env() -> None:
    """Settings must start normally in local development even with the placeholder secret."""
    s = Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        app_env="local",
        jwt_secret=_JWT_SECRET_PLACEHOLDER,
    )
    assert s.jwt_secret == _JWT_SECRET_PLACEHOLDER


def test_settings_allows_custom_jwt_secret_in_production() -> None:
    """Settings must start normally in production when a custom JWT secret is supplied."""
    s = Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        app_env="production",
        jwt_secret="a-very-long-and-random-secret-for-production",  # noqa: S106
    )
    assert s.app_env == "production"
