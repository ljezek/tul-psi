from __future__ import annotations

from typing import Any


class TokenProvider:
    """Provides and caches Entra ID tokens for Azure Database for PostgreSQL."""

    def __init__(self) -> None:
        from azure.identity.aio import DefaultAzureCredential

        from settings import get_settings

        settings = get_settings()

        # For User Assigned Managed Identity, we MUST provide the client ID.
        # If it is None, DefaultAzureCredential will try System Assigned identity.
        self.credential = DefaultAzureCredential(
            managed_identity_client_id=settings.azure_client_id
        )
        self._token: Any = None

    async def get_token(self) -> str:
        import time

        # Refresh token 5 minutes before expiry
        if not self._token or self._token.expires_on < (time.time() + 300):
            # The scope for Azure Database for PostgreSQL is always the same.
            self._token = await self.credential.get_token(
                "https://ossrdbms-aad.database.windows.net/.default"
            )
        return self._token.token
