from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from settings import get_settings


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
            self._token = await self.credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        return self._token.token


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    """Create and cache the async session factory on first call.

    Deferring engine creation to first use — rather than at module import time —
    means that importing this module does not require DATABASE_URL to be set.
    This keeps unit tests (which mock get_session) free of real DB configuration.
    """
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        # echo=False keeps SQL statements out of the production log stream;
        # set to True temporarily when debugging query issues locally.
        echo=False,
    )

    if settings.azure_managed_identity_enabled:
        token_provider = TokenProvider()

        @event.listens_for(engine.sync_engine, "connect")
        def add_token(dbapi_connection: Any, connection_record: Any) -> None:
            """Inject the Entra ID token into the connection parameters.

            Since the engine is async but SQLAlchemy events for 'connect' on
            the sync_engine (which wraps the pool) are synchronous, we must
            use a trick to get the token. However, asyncpg supports passing
            a 'password' that can be a callable or a string.
            """
            # For asyncpg, we can't easily use the sync event to await a token.
            # Instead, we configure the engine to use a dynamic password.
            pass

        # Re-create engine with dynamic password for asyncpg
        async def get_password() -> str:
            return await token_provider.get_token()

        engine = create_async_engine(
            settings.database_url,
            password=get_password,
            echo=False,
        )

    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for use as a FastAPI dependency.

    Usage in a route::

        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_session)) -> ...:
            ...

    The session is automatically closed when the request completes (or raises).
    """
    async with _session_factory()() as session:
        yield session
