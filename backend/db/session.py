from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from settings import get_settings


@lru_cache
def _get_engine() -> Engine:
    """Return a cached SQLAlchemy engine built from application settings.

    The engine is created once per process and reused for all requests.
    """
    return create_engine(get_settings().database_url)


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session and close it after the request.

    Intended for use as a FastAPI ``Depends()`` dependency.
    """
    with Session(_get_engine()) as session:
        yield session
