from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlmodel import Session

from settings import Settings, get_settings


@lru_cache
def _get_engine(database_url: str) -> Engine:
    """Return a cached SQLAlchemy engine for the given URL.

    The engine is created once per unique URL so that the connection pool
    is shared across requests rather than recreated on every call.
    """
    return create_engine(database_url)


def get_session(settings: Settings = Depends(get_settings)) -> Generator[Session, None, None]:
    """Yield a database session for use in a single request.

    FastAPI will call this generator as a dependency, injecting a fresh
    ``Session`` and ensuring it is closed when the request completes.
    """
    engine = _get_engine(settings.database_url)
    with Session(engine) as session:
        yield session
