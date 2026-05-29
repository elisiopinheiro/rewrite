"""Root conftest — shared test fixtures."""

import base64
from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.core.db import get_db
from app.main import app
from app.models.base import Base

# API version prefix — single source of truth for all tests
API = "/v3"


def make_basic_auth_headers(username: str, password: str) -> dict[str, str]:
    """Build Basic auth headers for test clients."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


@contextmanager
def _client_with_session(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client while overriding only the DB dependency."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield session

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as tc:
            yield tc
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


@pytest.fixture(name="engine", scope="session")
def fixture_engine() -> Generator[Engine, None, None]:
    """Ephemeral PostgreSQL engine shared across the test session."""
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        engine = create_engine(postgres.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


def _reset_database(engine: Engine) -> None:
    """Reset schema for tests that exercise the database."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture(name="session")
def fixture_session(engine: Engine) -> Generator[Session, None, None]:
    """Database session scoped to a single test with a clean schema."""
    _reset_database(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def fixture_client(session: Session) -> Generator[TestClient, None, None]:
    """Test client with the DB dependency overridden for one test."""
    with _client_with_session(session) as tc:
        yield tc


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Basic auth headers using default dev credentials."""
    return make_basic_auth_headers("4wm", "4wm")


@pytest.fixture()
def authed_client(session: Session, auth_headers: dict[str, str]) -> Generator[TestClient, None, None]:
    """Dedicated client with auth headers pre-set on every request."""
    with _client_with_session(session) as tc:
        tc.headers.update(auth_headers)
        yield tc
