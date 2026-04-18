from __future__ import annotations

from typing import Any


class TokenProvider:
    """Provides and caches Entra ID tokens for Azure Database for PostgreSQL."""

    def __init__(self) -> None:
        from azure.identity.aio import DefaultAzureCredential

        self.credential = DefaultAzureCredential()
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
