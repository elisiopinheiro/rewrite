"""v3 schema compatibility — align the shared schema with clusters-metadata-api

Revision ID: 73aee50345b2
Revises: 5e67ef3550c0
Create Date: 2026-05-21 10:00:00.000000

One-time compatibility migration so the legacy clusters-4wm service and the new
clusters-metadata-api can share this database. After this revision the rewrite
owns schema migrations and legacy is frozen.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "73aee50345b2"
down_revision = "5e67ef3550c0"
branch_labels = None
depends_on = None

# (existing_fk_name, table, column) -> recreated with ondelete=CASCADE
_CLUSTER_FKS = [
    ("additionalnodepool_cluster_id_fkey", "additionalnodepool"),
    ("clientnamespace_cluster_id_fkey", "clientnamespace"),
    ("clientotlpendpoint_cluster_id_fkey", "clientotlpendpoint"),
    ("userfeature_cluster_id_fkey", "userfeature"),
    ("clusterfeature_cluster_id_fkey", "clusterfeature"),
]


def upgrade() -> None:
    # --- backfill nullable columns that become NOT NULL ---
    op.execute("UPDATE cluster SET status = 'running' WHERE status IS NULL")
    op.execute("UPDATE feature SET type = 'optional' WHERE type IS NULL")
    op.execute("UPDATE clusterfeature SET enabled = false WHERE enabled IS NULL")
    op.execute("UPDATE release SET reserved_namespaces = '[]'::json WHERE reserved_namespaces IS NULL")

    # --- NOT NULL ---
    op.alter_column("cluster", "status", existing_type=sa.String(), nullable=False)
    op.alter_column("feature", "type", existing_type=sa.String(), nullable=False)
    op.alter_column("clusterfeature", "enabled", existing_type=sa.Boolean(), nullable=False)
    op.alter_column("release", "reserved_namespaces", existing_type=sa.JSON(), nullable=False)
    op.alter_column("additionalnodepool", "cluster_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("clientnamespace", "cluster_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("clientotlpendpoint", "cluster_id", existing_type=sa.Integer(), nullable=False)

    # --- account_name becomes optional ---
    op.alter_column("cluster", "account_name", existing_type=sa.String(), nullable=True)

    # --- drop deprecated kubedownscaler columns (superseded by uptime_period) ---
    op.drop_column("cluster", "kubedownscaler_upscale_period")
    op.drop_column("cluster", "kubedownscaler_downscale_period")

    # --- normalize unique constraint names + add feature(name) uniqueness ---
    op.drop_constraint("cluster_repository_key", "cluster", type_="unique")
    op.create_unique_constraint("cluster_repository_uc", "cluster", ["repository"])
    op.drop_constraint("teamswebhook_webhook_id_key", "teamswebhook", type_="unique")
    op.create_unique_constraint("teamswebhook_webhook_id_uc", "teamswebhook", ["webhook_id"])
    op.create_unique_constraint("feature_name_uc", "feature", ["name"])

    # --- child FKs gain ON DELETE CASCADE ---
    for name, table in _CLUSTER_FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, "cluster", ["cluster_id"], ["id"], ondelete="CASCADE")
    op.drop_constraint("clusterfeature_feature_id_fkey", "clusterfeature", type_="foreignkey")
    op.create_foreign_key(
        "clusterfeature_feature_id_fkey", "clusterfeature", "feature", ["feature_id"], ["id"], ondelete="CASCADE"
    )
    op.drop_constraint("releasefeature_release_id_fkey", "releasefeature", type_="foreignkey")
    op.create_foreign_key(
        "releasefeature_release_id_fkey", "releasefeature", "release", ["release_id"], ["id"], ondelete="CASCADE"
    )
    op.drop_constraint("releasefeature_feature_id_fkey", "releasefeature", type_="foreignkey")
    op.create_foreign_key(
        "releasefeature_feature_id_fkey", "releasefeature", "feature", ["feature_id"], ["id"], ondelete="CASCADE"
    )

    # --- clusterlock: re-key from cluster_name to cluster_id ---
    op.add_column("clusterlock", sa.Column("cluster_id", sa.Integer(), nullable=True))
    op.execute("UPDATE clusterlock SET cluster_id = c.id FROM cluster c WHERE clusterlock.cluster_name = c.name")
    op.execute("DELETE FROM clusterlock WHERE cluster_id IS NULL")
    op.alter_column("clusterlock", "cluster_id", nullable=False)
    op.drop_constraint("clusterlock_pkey", "clusterlock", type_="primary")
    op.drop_constraint("clusterlock_cluster_name_fkey", "clusterlock", type_="foreignkey")
    op.drop_column("clusterlock", "cluster_name")
    op.create_primary_key("clusterlock_pkey", "clusterlock", ["cluster_id"])
    op.create_foreign_key(
        "clusterlock_cluster_id_fkey", "clusterlock", "cluster", ["cluster_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    # clusterlock: back to cluster_name PK
    op.add_column("clusterlock", sa.Column("cluster_name", sa.String(), nullable=True))
    op.execute("UPDATE clusterlock SET cluster_name = c.name FROM cluster c WHERE clusterlock.cluster_id = c.id")
    op.alter_column("clusterlock", "cluster_name", nullable=False)
    op.drop_constraint("clusterlock_cluster_id_fkey", "clusterlock", type_="foreignkey")
    op.drop_constraint("clusterlock_pkey", "clusterlock", type_="primary")
    op.drop_column("clusterlock", "cluster_id")
    op.create_primary_key("clusterlock_pkey", "clusterlock", ["cluster_name"])
    op.create_foreign_key("clusterlock_cluster_name_fkey", "clusterlock", "cluster", ["cluster_name"], ["name"])

    # FKs back to no ondelete
    op.drop_constraint("releasefeature_feature_id_fkey", "releasefeature", type_="foreignkey")
    op.create_foreign_key("releasefeature_feature_id_fkey", "releasefeature", "feature", ["feature_id"], ["id"])
    op.drop_constraint("releasefeature_release_id_fkey", "releasefeature", type_="foreignkey")
    op.create_foreign_key("releasefeature_release_id_fkey", "releasefeature", "release", ["release_id"], ["id"])
    op.drop_constraint("clusterfeature_feature_id_fkey", "clusterfeature", type_="foreignkey")
    op.create_foreign_key("clusterfeature_feature_id_fkey", "clusterfeature", "feature", ["feature_id"], ["id"])
    for name, table in _CLUSTER_FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, "cluster", ["cluster_id"], ["id"])

    op.drop_constraint("feature_name_uc", "feature", type_="unique")
    op.drop_constraint("teamswebhook_webhook_id_uc", "teamswebhook", type_="unique")
    op.create_unique_constraint("teamswebhook_webhook_id_key", "teamswebhook", ["webhook_id"])
    op.drop_constraint("cluster_repository_uc", "cluster", type_="unique")
    op.create_unique_constraint("cluster_repository_key", "cluster", ["repository"])

    op.add_column("cluster", sa.Column("kubedownscaler_downscale_period", sa.String(), nullable=True))
    op.add_column("cluster", sa.Column("kubedownscaler_upscale_period", sa.String(), nullable=True))

    op.alter_column("cluster", "account_name", existing_type=sa.String(), nullable=False)
    op.alter_column("additionalnodepool", "cluster_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("clientnamespace", "cluster_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("clientotlpendpoint", "cluster_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("release", "reserved_namespaces", existing_type=sa.JSON(), nullable=True)
    op.alter_column("clusterfeature", "enabled", existing_type=sa.Boolean(), nullable=True)
    op.alter_column("feature", "type", existing_type=sa.String(), nullable=True)
    op.alter_column("cluster", "status", existing_type=sa.String(), nullable=True)
