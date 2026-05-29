import logging
import os

import sqlalchemy
from sqlmodel import Session, create_engine

from api.shared.config import DATABASE_LOGGING_LEVEL
from api.shared.enums import LoggingLevel
from api.shared.logger import logger

# Get database parameters
DB_DRIVER_NAME = "postgresql"
DB_NAME = os.environ.get("DB_NAME", "database")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USERNAME = os.environ.get("DB_USERNAME", "username")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_PORT = os.environ.get("DB_PORT", "5432")


connection_url = sqlalchemy.engine.URL.create(
    drivername=DB_DRIVER_NAME, username=DB_USERNAME, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME, port=DB_PORT
)

engine = create_engine(connection_url)

db_log_level = LoggingLevel.DEFAULT

try:
    db_log_level = LoggingLevel(DATABASE_LOGGING_LEVEL)
except Exception:
    logger.error(f"Invalid DB Logging Level: {DATABASE_LOGGING_LEVEL}")

logger.info(f"Setting database logging level to: {db_log_level}")
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(db_log_level)


def get_db():
    with Session(engine) as session:
        yield session
