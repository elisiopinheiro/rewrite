"""Squashed baseline for the Clusters Metadata API.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-19 10:00:00.000000

This single revision collapses the entire legacy Alembic chain
(``305ae638786e`` .. ``a1b2c3d4e5f6``) into one frozen baseline. Its revision id
is deliberately the head the production database is already stamped at, so
``alembic upgrade head`` is a **no-op** on every already-migrated environment and
the rewrite deploys without running a migration against the shared database.

On a fresh/empty database (local dev, CI, a new region) ``upgrade()`` builds the
full schema and recreates the ``updated_at`` trigger the legacy chain installed,
so a freshly-bootstrapped database matches the migrated production schema.

The table DDL was produced with ``alembic revision --autogenerate`` against the
ORM models and then frozen; it is intentionally explicit (not ``create_all``) so
later migrations apply cleanly on a fresh database.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None

# Reproduces legacy revisions db119f72f5d3 (function) and 37f752684c65 (trigger on
# the cluster table). Triggers/functions are not part of the ORM metadata, so they
# must be created explicitly for fresh databases to match production.
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
    op.create_table(
        "cluster",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("subscription", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("release", sa.String(), nullable=False),
        sa.Column("environment", sa.String(), nullable=False),
        sa.Column("internal", sa.Boolean(), nullable=False),
        sa.Column("repository", sa.String(), nullable=False),
        sa.Column("multi_tenant", sa.Boolean(), nullable=False),
        sa.Column("node_min_count", sa.Integer(), nullable=False),
        sa.Column("node_max_count", sa.Integer(), nullable=False),
        sa.Column("provider_region", sa.String(), nullable=False),
        sa.Column("tshirt_size", sa.String(), nullable=False),
        sa.Column("infra_revision", sa.String(), nullable=False),
        sa.Column("kubernetes_version", sa.String(), nullable=False),
        sa.Column("network_cidr", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="running", nullable=False),
        sa.Column("gateway_api_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("headlamp_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("account_name", sa.String(), nullable=True),
        sa.Column("appd_id", sa.String(), nullable=True),
        sa.Column("dns_zone", sa.String(), nullable=True),
        sa.Column("owner_group", sa.String(), nullable=True),
        sa.Column("cmdb_app_id", sa.String(), nullable=True),
        sa.Column("cmdb_appd_id", sa.String(), nullable=True),
        sa.Column("pod_cidr", sa.String(), nullable=True),
        sa.Column("service_cidr", sa.String(), nullable=True),
        sa.Column("logging_retention_period", sa.String(), nullable=True),
        sa.Column("tracing_retention_period", sa.String(), nullable=True),
        sa.Column("uptime_period", sa.String(), nullable=True),
        sa.Column("domain_allowlist", sa.JSON(), nullable=True),
        sa.Column("authorized_api_ip_ranges", sa.JSON(), nullable=True),
        sa.Column("aws_vpc", sa.String(), nullable=True),
        sa.Column("aws_vpc_endpoint_remote_account_ids", sa.JSON(), nullable=True),
        sa.Column("aws_remote_account_ids", sa.JSON(), nullable=True),
        sa.Column("vpc_endpoint_service_name", sa.String(), nullable=True),
        sa.Column("vpc_endpoint_service_ingress_name", sa.String(), nullable=True),
        sa.Column("cluster_oidc_issuer_url", sa.String(), nullable=True),
        sa.Column("azure_sku_tier", sa.String(), nullable=True),
        sa.Column("azure_subnet_name", sa.String(), nullable=True),
        sa.Column("azure_vnet_name", sa.String(), nullable=True),
        sa.Column("azure_vnet_resource_group", sa.String(), nullable=True),
        sa.Column("dns_service_ip", sa.String(), nullable=True),
        sa.Column("mi_agentpool_object_id", sa.String(), nullable=True),
        sa.Column("mi_cluster_object_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="cluster_name_uc"),
        sa.UniqueConstraint("repository", name="cluster_repository_uc"),
    )
    op.create_table(
        "feature",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("constraints", sa.JSON(), server_default=sa.text("'[]'"), nullable=True),
        sa.Column("namespaced", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="feature_name_uc"),
    )
    op.create_table(
        "release",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("reserved_namespaces", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "provider", name="release_name_provider_uc"),
    )
    op.create_table(
        "additionalnodepool",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("node_min_count", sa.Integer(), nullable=False),
        sa.Column("node_max_count", sa.Integer(), nullable=False),
        sa.Column("tshirt_size", sa.String(), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_additionalnodepool_cluster_id"), "additionalnodepool", ["cluster_id"], unique=False)
    op.create_table(
        "clientnamespace",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("consumed_by", sa.String(), nullable=True),
        sa.Column("admin", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("viewer", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("editor", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clientnamespace_cluster_id"), "clientnamespace", ["cluster_id"], unique=False)
    op.create_table(
        "clientotlpendpoint",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("auth", sa.JSON(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clientotlpendpoint_cluster_id"), "clientotlpendpoint", ["cluster_id"], unique=False)
    op.create_table(
        "clusterfeature",
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("feature_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feature_id"], ["feature.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cluster_id", "feature_id"),
    )
    op.create_table(
        "clusterlock",
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("owner", sa.String(), nullable=True),
        sa.Column("token", sa.String(), nullable=True),
        sa.Column("timeout_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cluster_id"),
    )
    op.create_table(
        "operation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("cicd_url", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("cluster_repository", sa.String(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operation_cluster_id"), "operation", ["cluster_id"], unique=False)
    op.create_table(
        "releasefeature",
        sa.Column("release_id", sa.Integer(), nullable=False),
        sa.Column("feature_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["feature_id"], ["feature.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["release_id"], ["release.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("release_id", "feature_id"),
    )
    op.create_table(
        "storageclass",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_storageclass_cluster_id"), "storageclass", ["cluster_id"], unique=False)
    op.create_table(
        "teamswebhook",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("webhook_id", sa.UUID(), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("webhook_id", name="teamswebhook_webhook_id_uc"),
    )
    op.create_index(op.f("ix_teamswebhook_cluster_id"), "teamswebhook", ["cluster_id"], unique=False)
    op.create_table(
        "userfeature",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(), nullable=False),
        sa.Column("repo_url", sa.String(), nullable=False),
        sa.Column("commit_hash", sa.String(), nullable=False),
        sa.Column("helm_path", sa.String(), nullable=True),
        sa.Column("values_path", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["cluster.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("name", "cluster_id"),
    )

    op.execute(_CREATE_UPDATED_AT_FUNCTION)
    op.execute(_CREATE_UPDATED_AT_TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS cluster_set_updated_at_on_update ON cluster;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

    op.drop_table("userfeature")
    op.drop_index(op.f("ix_teamswebhook_cluster_id"), table_name="teamswebhook")
    op.drop_table("teamswebhook")
    op.drop_index(op.f("ix_storageclass_cluster_id"), table_name="storageclass")
    op.drop_table("storageclass")
    op.drop_table("releasefeature")
    op.drop_index(op.f("ix_operation_cluster_id"), table_name="operation")
    op.drop_table("operation")
    op.drop_table("clusterlock")
    op.drop_table("clusterfeature")
    op.drop_index(op.f("ix_clientotlpendpoint_cluster_id"), table_name="clientotlpendpoint")
    op.drop_table("clientotlpendpoint")
    op.drop_index(op.f("ix_clientnamespace_cluster_id"), table_name="clientnamespace")
    op.drop_table("clientnamespace")
    op.drop_index(op.f("ix_additionalnodepool_cluster_id"), table_name="additionalnodepool")
    op.drop_table("additionalnodepool")
    op.drop_table("release")
    op.drop_table("feature")
    op.drop_table("cluster")
