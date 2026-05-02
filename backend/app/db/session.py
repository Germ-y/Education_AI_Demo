from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.domain.db_models import Base


def create_database_engine(database_url: str) -> Engine:
    connect_args = {}
    engine_kwargs = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if database_url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, future=True, **engine_kwargs)


@lru_cache
def get_engine() -> Engine:
    return create_database_engine(get_settings().database_url)


@lru_cache
def get_session_maker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)


def create_schema(engine: Engine | None = None) -> None:
    Base.metadata.create_all(bind=engine or get_engine())


def drop_schema(engine: Engine | None = None) -> None:
    Base.metadata.drop_all(bind=engine or get_engine())


def get_db_session() -> Iterator[Session]:
    session_factory = get_session_maker()
    with session_factory() as session:
        yield session
