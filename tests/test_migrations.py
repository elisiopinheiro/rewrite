"""Migration invariants that protect the shared-DB deploy-as-no-op contract."""

from collections.abc import Generator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine, inspect
from testcontainers.postgres import PostgresContainer

from app.models.base import Base

# The revision the production database is already stamped at via the legacy
# service. The rewrite baseline MUST match it so `alembic upgrade head` is a
# no-op on prod and the rewrite deploys without running a migration.
PROD_HEAD = "73aee50345b2"


def _alembic_config(url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", "migrations")
    if url is not None:
        cfg.attributes["sqlalchemy.url"] = url
    return cfg


def test_single_head_equals_prod_head() -> None:
    script = ScriptDirectory.from_config(_alembic_config())
    assert script.get_current_head() == PROD_HEAD


@pytest.fixture(scope="module")
def migrated_engine() -> Generator[Engine, None, None]:
    """A fresh database built by running the baseline migration (not create_all)."""
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        url = postgres.get_connection_url()
        command.upgrade(_alembic_config(url), "head")
        engine = create_engine(url)
        yield engine
        engine.dispose()


def test_baseline_builds_schema_matching_orm(migrated_engine: Engine) -> None:
    """A DB built by the baseline must match the ORM (no add/remove of tables or columns)."""
    with migrated_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, Base.metadata)

    structural = [d for d in diffs if d[0] in {"add_table", "remove_table", "add_column", "remove_column"}]
    assert structural == [], f"baseline/ORM schema drift: {structural}"


def test_baseline_installs_updated_at_trigger(migrated_engine: Engine) -> None:
    """The legacy updated_at trigger must be reproduced for fresh databases."""
    inspector = inspect(migrated_engine)
    assert "cluster" in inspector.get_table_names()
    with migrated_engine.connect() as connection:
        trigger = connection.exec_driver_sql(
            "SELECT 1 FROM pg_trigger WHERE tgname = 'cluster_set_updated_at_on_update'"
        ).first()
    assert trigger is not None
