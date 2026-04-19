from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.identity.aio import DefaultAzureCredential

from db.session import _session_factory
from db.token_provider import TokenProvider
from settings import Settings


@pytest.mark.asyncio
async def test_token_provider_returns_token():
    """Verify that TokenProvider calls DefaultAzureCredential with the correct scope."""
    mock_token = MagicMock()
    mock_token.token = "mock-token-123"  # noqa: S105
    mock_token.expires_on = 9999999999  # Far in the future

    with patch.object(
        DefaultAzureCredential, "get_token", new_callable=AsyncMock
    ) as mock_get_token:
        mock_get_token.return_value = mock_token

        provider = TokenProvider()
        token = await provider.get_token()

        assert token == "mock-token-123"  # noqa: S105
        mock_get_token.assert_called_once_with(
            "https://ossrdbms-aad.database.windows.net/.default"
        )



@pytest.mark.asyncio
async def test_session_factory_uses_token_provider_when_enabled():
    """Verify that _session_factory configures the engine with the token provider's callable."""
    # 1. Prepare mock settings
    mock_settings = Settings(
        database_url="postgresql+asyncpg://localhost/test",
        azure_managed_identity_enabled=True,
        app_env="dev",
    )

    # 2. Patch get_settings and clear lru_cache for _session_factory
    with (
        patch("db.session.get_settings", return_value=mock_settings),
        patch("db.session.create_async_engine") as mock_create_engine,
    ):
        # Clear cache to force re-creation of the engine with mock settings
        _session_factory.cache_clear()

        _session_factory()

        # 3. Assert that create_async_engine was called with the correct connect_args
        mock_create_engine.assert_called_once()
        args, kwargs = mock_create_engine.call_args

        assert args[0] == "postgresql+asyncpg://localhost/test"
        assert "connect_args" in kwargs
        assert kwargs["connect_args"]["ssl"] is True

        # Verify 'password' is a callable (the get_token method)
        password_callable = kwargs["connect_args"]["password"]
        assert callable(password_callable)
        # It should be bound to a TokenProvider instance
        assert "TokenProvider.get_token" in str(password_callable)


@pytest.mark.asyncio
async def test_session_factory_forces_ssl_in_non_local_env():
    """Verify that SSL is forced in non-local environments even without Managed Identity."""
    mock_settings = Settings(
        database_url="postgresql+asyncpg://localhost/test",
        azure_managed_identity_enabled=False,
        app_env="dev",
    )

    with (
        patch("db.session.get_settings", return_value=mock_settings),
        patch("db.session.create_async_engine") as mock_create_engine,
    ):
        _session_factory.cache_clear()
        _session_factory()

        _, kwargs = mock_create_engine.call_args
        assert kwargs["connect_args"]["ssl"] is True
