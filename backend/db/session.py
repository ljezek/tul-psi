from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from settings import get_settings

# The async engine is the single connection pool for the whole application.
# It is created once at module import time and reused for all requests.
engine = create_async_engine(
    get_settings().database_url,
    # echo=False keeps SQL statements out of the production log stream;
    # set to True temporarily when debugging query issues locally.
    echo=False,
)

# async_session_factory produces AsyncSession instances that are compatible with
# FastAPI's dependency-injection system via the get_session dependency below.
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for use as a FastAPI dependency.

    Usage in a route::

        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_session)) -> ...:
            ...

    The session is automatically closed when the request completes (or raises).
    """
    async with async_session_factory() as session:
        yield session
