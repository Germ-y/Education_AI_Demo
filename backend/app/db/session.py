from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import BACKEND_DIR, get_settings
from app.domain.db_models import Base


def normalize_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return database_url

    database_path = Path(url.database)
    if database_path.is_absolute():
        return database_url

    resolved_path = (BACKEND_DIR / database_path).resolve()
    return url.set(database=resolved_path.as_posix()).render_as_string(hide_password=False)


def create_database_engine(database_url: str) -> Engine:
    database_url = normalize_database_url(database_url)
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
    active_engine = engine or get_engine()
    Base.metadata.create_all(bind=active_engine)
    add_missing_demo_columns(active_engine)


def add_missing_demo_columns(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "students" not in existing_tables or "support_cases" not in existing_tables:
        return

    support_case_columns = {column["name"] for column in inspector.get_columns("support_cases")}
    statements = []

    if "dashboard_stage" not in support_case_columns:
        statements.append("ALTER TABLE support_cases ADD COLUMN dashboard_stage VARCHAR DEFAULT 'initial_review'")
    if "support_strategy" not in support_case_columns:
        statements.append("ALTER TABLE support_cases ADD COLUMN support_strategy TEXT")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def drop_schema(engine: Engine | None = None) -> None:
    Base.metadata.drop_all(bind=engine or get_engine())


def get_db_session() -> Iterator[Session]:
    session_factory = get_session_maker()
    with session_factory() as session:
        yield session
