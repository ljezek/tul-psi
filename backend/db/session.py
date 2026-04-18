from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.token_provider import TokenProvider
from settings import get_settings


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    """Create and cache the async session factory on first call.

    Deferring engine creation to first use — rather than at module import time —
    means that importing this module does not require DATABASE_URL to be set.
    This keeps unit tests (which mock get_session) free of real DB configuration.
    """
    settings = get_settings()

    # Base configuration for the engine.
    engine_kwargs: dict[str, Any] = {
        "echo": False,
    }

    if settings.azure_managed_identity_enabled:
        token_provider = TokenProvider()

        # asyncpg supports passing a 'password' that is an async callable.
        # This is the standard way to handle Entra ID (Managed Identity) tokens,
        # as it allows the driver to refresh the token automatically before
        # establishing new connections in the pool.
        engine_kwargs["connect_args"] = {"password": token_provider.get_token}

    engine = create_async_engine(
        settings.database_url,
        **engine_kwargs,
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
