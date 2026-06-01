"""Squashed baseline for the Clusters Metadata API.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-19 10:00:00.000000

This single revision collapses the entire legacy Alembic chain
(``305ae638786e`` .. ``a1b2c3d4e5f6``) into one baseline. Its revision id is
deliberately set to ``a1b2c3d4e5f6`` — the head the production database is
already stamped at via the legacy service — so that ``alembic upgrade head``
is a **no-op** on every already-migrated environment and the rewrite deploys
without running a migration against the shared production database.

On a fresh/empty database (local dev, CI, a new region) ``upgrade()`` builds
the full schema from the ORM metadata and recreates the ``updated_at`` trigger
that the legacy chain installed, so a freshly-bootstrapped database matches the
migrated production schema.
"""

from alembic import op

from app.models.base import Base

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None

# Reproduces legacy revisions db119f72f5d3 (function) and 37f752684c65 (trigger
# on the cluster table) so fresh databases get an auto-managed updated_at.
_CREATE_UPDATED_AT_FUNCTION = """
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
"""

_CREATE_UPDATED_AT_TRIGGER = """
DROP TRIGGER IF EXISTS cluster_set_updated_at_on_update ON cluster;
CREATE TRIGGER cluster_set_updated_at_on_update
    BEFORE UPDATE ON cluster
    FOR EACH ROW
    EXECUTE PROCEDURE set_updated_at();
"""


def upgrade() -> None:
    bind = op.get_bind()
    # checkfirst=True (the default) makes this a no-op against the already
    # migrated prod schema and a full build on an empty database.
    Base.metadata.create_all(bind)
    op.execute(_CREATE_UPDATED_AT_FUNCTION)
    op.execute(_CREATE_UPDATED_AT_TRIGGER)


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("DROP TRIGGER IF EXISTS cluster_set_updated_at_on_update ON cluster;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
    Base.metadata.drop_all(bind)
