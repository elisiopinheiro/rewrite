import os
from base64 import b64encode

import pytest
from alembic import command
from alembic.config import Config
from factories.cluster_factory import (
    AdditionalNodePoolFactory,
    AWSClusterFactory,
    AzureClusterFactory,
    ClientNamespaceFactory,
    TeamsWebhookFactory,
)
from factories.feature_factory import FeatureFactory
from factories.otlp_endpoint_factory import ClientOTLPEndpointFactory
from factories.release_factory import ReleaseFactory
from factories.storage_class_factory import RemoteStorageClassFactory, UltraSSDStorageClassFactory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from api.m4w.main import app
from api.partner.main import app as partner_app
from api.shared import database

M4W_CREDENTIALS = "ctw:ctw"
SCP_CREDENTIALS = "scp:scp"
CF_CREDENTIALS = "cf:cf"
SOLAR_CREDENTIALS = "solar:solar"


@pytest.fixture(scope="session")
def postgres_container():
    """Start and initialize a Postgres test container.

    This fixture:
    - Creates a PostgreSQL container using testcontainers
    - Initializes the database with all SQLModel tables
    - Overrides the default database engine
    - Yields a dictionary containing the engine and connection URL
    - Automatically cleans up the container and disposes the engine after tests

    Returns:
        dict: A dictionary containing:
            - engine: SQLAlchemy engine instance
            - connection_url: Database connection URL

    Note:
        This fixture has session scope, meaning the container is created once
        for the entire test session and shared across all tests.
    """
    with PostgresContainer("postgres:14.2", username="test", password="test", dbname="test_db") as container:
        connection_url = container.get_connection_url()
        engine = create_engine(connection_url)

        # path to alembic.ini file
        path_to_current_dir = os.path.dirname(__file__)
        alembic_cfg_path = os.path.join(path_to_current_dir, "..", "alembic.ini")
        alembic_cfg = Config(alembic_cfg_path)
        # alembic Migration
        alembic_cfg.set_main_option("sqlalchemy.url", connection_url)

        command.upgrade(alembic_cfg, "head")

        yield {
            "engine": engine,
            "connection_url": container.get_connection_url(),
        }

        engine.dispose()


@pytest.fixture(scope="function")
def db_session(postgres_container):
    """Create a database session for testing with automatic rollback.

    This fixture:
    - Creates a new database session for each test
    - Wraps the session in a transaction
    - Automatically rolls back changes after each test
    - Ensures test isolation

    Args:
        postgres_container: The postgres container fixture that provides the database engine

    Returns:
        Session: A SQLAlchemy session object

    Note:
        This fixture has function scope, meaning a new session is created
        for each test function.
    """
    engine = postgres_container["engine"]
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)
    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def set_session_for_factories(db_session):
    AWSClusterFactory._meta.sqlalchemy_session = db_session
    FeatureFactory._meta.sqlalchemy_session = db_session
    AzureClusterFactory._meta.sqlalchemy_session = db_session
    TeamsWebhookFactory._meta.sqlalchemy_session = db_session
    ClientNamespaceFactory._meta.sqlalchemy_session = db_session
    ReleaseFactory._meta.sqlalchemy_session = db_session
    AdditionalNodePoolFactory._meta.sqlalchemy_session = db_session
    # Storage Classes
    RemoteStorageClassFactory._meta.sqlalchemy_session = db_session
    UltraSSDStorageClassFactory._meta.sqlalchemy_session = db_session
    # OTLP Endpoints
    ClientOTLPEndpointFactory._meta.sqlalchemy_session = db_session


# Test Client for clusters-4wm API
@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database session.

    This fixture:
    - Creates a FastAPI TestClient
    - Overrides the database dependency to use the test session
    - Cleans up overrides after the test

    Args:
        db_session: The database session fixture

    Returns:
        TestClient: A FastAPI test client instance
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """Create an authenticated test client with basic auth.

    This fixture:
    - Takes a base test client
    - Adds Basic Authentication headers
    - Cleans up headers after the test

    Args:
        client: The base test client fixture

    Returns:
        TestClient: An authenticated FastAPI test client instance
    """
    credentials = b64encode(M4W_CREDENTIALS.encode("utf-8")).decode("utf-8")
    client.headers.update({"Authorization": f"Basic {credentials}"})
    yield client
    client.headers.clear()


@pytest.fixture
def unauth_client(client):
    """Create an unauthenticated test client.

    This fixture:
    - Takes a base test client
    - Ensures no authentication headers are present
    - Cleans up headers after the test

    Args:
        client: The base test client fixture

    Returns:
        TestClient: An unauthenticated FastAPI test client instance
    """
    client.headers.clear()
    yield client
    client.headers.clear()


# Test Client for clusters-4wm-partner API
@pytest.fixture(scope="function")
def partner_client(db_session):
    """Create a test client with overridden database session.

    This fixture:
    - Creates a FastAPI TestClient
    - Overrides the database dependency to use the test session
    - Cleans up overrides after the test

    Args:
        db_session: The database session fixture

    Returns:
        TestClient: A FastAPI test client instance
    """

    def override_get_db():
        yield db_session

    partner_app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(partner_app) as c:
        yield c
    partner_app.dependency_overrides.clear()


@pytest.fixture
def auth_partner_client(partner_client, request):
    """Create an authenticated test client with basic auth.

    This fixture:
    - Takes a base test client
    - Adds Basic Authentication headers
    - Cleans up headers after the test

    Args:
        client: The base test client fixture

    Returns:
        TestClient: An authenticated FastAPI test client instance
    """
    credentials = b64encode((request.param).encode("utf-8")).decode("utf-8")
    partner_client.headers.update({"Authorization": f"Basic {credentials}"})
    yield partner_client
    partner_client.headers.clear()


@pytest.fixture
def unauth_partner_client(partner_client):
    """Create an unauthenticated test client.

    This fixture:
    - Takes a base test client
    - Ensures no authentication headers are present
    - Cleans up headers after the test

    Args:
        client: The base test client fixture

    Returns:
        TestClient: An unauthenticated FastAPI test client instance
    """
    partner_client.headers.clear()
    yield partner_client
    partner_client.headers.clear()
