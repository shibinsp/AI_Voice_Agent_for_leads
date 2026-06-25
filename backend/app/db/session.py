from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.models import entities  # noqa: F401


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    is_sqlite = settings.database_url.startswith("sqlite")
    return create_engine(
        settings.database_url,
        future=True,
        connect_args=_sqlite_connect_args(settings.database_url),
        # pre-ping recycles dead pooled connections (important for Postgres in production)
        pool_pre_ping=not is_sqlite,
    )


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())

