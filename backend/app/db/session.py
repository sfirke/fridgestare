from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

url = make_url(settings.database_url)
engine_kwargs: dict[str, Any] = {"future": True, "pool_pre_ping": True, "pool_recycle": 3600}
if url.get_backend_name() in ("mysql", "mariadb"):
    # MariaDB defaults to REPEATABLE READ; PostgreSQL used READ COMMITTED, which is
    # what long-lived sessions such as the scheduler's expect.
    engine_kwargs["isolation_level"] = "READ COMMITTED"

engine = create_engine(url, **engine_kwargs)
# Conventional SQLAlchemy/FastAPI name for a session factory, not a constant.
SessionLocal = sessionmaker(  # pylint: disable=invalid-name
    bind=engine, autocommit=False, autoflush=False, future=True
)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
