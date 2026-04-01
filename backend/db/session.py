from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from settings import get_settings


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    """Create and cache the async session factory on first call.

    Deferring engine creation to first use — rather than at module import time —
    means that importing this module does not require DATABASE_URL to be set.
    This keeps unit tests (which mock get_session) free of real DB configuration.
    """
    engine = create_async_engine(
        get_settings().database_url,
        # echo=False keeps SQL statements out of the production log stream;
        # set to True temporarily when debugging query issues locally.
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
