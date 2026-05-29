"""Database engine and session management."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_log_level = getattr(logging, settings.DATABASE_LOGGING_LEVEL, logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(_log_level)

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def database_is_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except SQLAlchemyError:
        return False

    return True


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
