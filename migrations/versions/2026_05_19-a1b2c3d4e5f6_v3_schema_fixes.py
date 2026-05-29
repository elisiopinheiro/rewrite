"""v3 schema fixes: nullability, FK cascade, lock table PK, drop deprecated columns

Revision ID: a1b2c3d4e5f6
Revises: 44775c618d1f
Create Date: 2026-05-19 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "44775c618d1f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    fix_empty_strings = [
        "vpc_endpoint_service_name",
        "vpc_endpoint_service_ingress_name",
        "cluster_oidc_issuer_url",
        "azure_subnet_name",
        "azure_vnet_name",
        "azure_vnet_resource_group",
        "dns_service_ip",
        "mi_agentpool_object_id",
        "mi_cluster_object_id",
        "account_name",
    ]
    for column in fix_empty_strings:
        op.execute(f"UPDATE cluster SET {column} = NULL WHERE {column} = ''")
        op.alter_column("cluster", column, server_default=None)

    op.alter_column("cluster", "account_name", existing_type=sa.String(), nullable=True)

    op.execute("UPDATE cluster SET aws_vpc = NULL WHERE aws_vpc = ''")

    op.execute("UPDATE feature SET type = 'optional' WHERE type IS NULL")
    op.execute("UPDATE feature SET namespaced = false WHERE namespaced IS NULL")
    op.alter_column("feature", "type", nullable=False)
    op.alter_column("feature", "namespaced", nullable=False)

    op.alter_column("additionalnodepool", "cluster_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("clientnamespace", "cluster_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("clientotlpendpoint", "cluster_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("cluster", "status", existing_type=sa.String(), nullable=False)
    op.alter_column("clusterfeature", "enabled", existing_type=sa.Boolean(), nullable=False)
    op.alter_column("release", "reserved_namespaces", existing_type=sa.JSON(), nullable=False)

    op.drop_constraint("cluster_repository_key", "cluster", type_="unique")
    op.create_unique_constraint("cluster_repository_uc", "cluster", ["repository"])

    op.drop_constraint("teamswebhook_webhook_id_key", "teamswebhook", type_="unique")
    op.create_unique_constraint("teamswebhook_webhook_id_uc", "teamswebhook", ["webhook_id"])

    op.create_unique_constraint("feature_name_uc", "feature", ["name"])

    op.drop_constraint("clusterfeature_cluster_id_fkey", "clusterfeature", type_="foreignkey")
    op.create_foreign_key(
        "clusterfeature_cluster_id_fkey",
        "clusterfeature",
        "cluster",
        ["cluster_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("clusterfeature_feature_id_fkey", "clusterfeature", type_="foreignkey")
    op.create_foreign_key(
        "clusterfeature_feature_id_fkey",
        "clusterfeature",
        "feature",
        ["feature_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("releasefeature_release_id_fkey", "releasefeature", type_="foreignkey")
    op.create_foreign_key(
        "releasefeature_release_id_fkey",
        "releasefeature",
        "release",
        ["release_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("releasefeature_feature_id_fkey", "releasefeature", type_="foreignkey")
    op.create_foreign_key(
        "releasefeature_feature_id_fkey",
        "releasefeature",
        "feature",
        ["feature_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("userfeature_cluster_id_fkey", "userfeature", type_="foreignkey")
    op.create_foreign_key(
        "userfeature_cluster_id_fkey",
        "userfeature",
        "cluster",
        ["cluster_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("clientotlpendpoint_cluster_id_fkey", "clientotlpendpoint", type_="foreignkey")
    op.create_foreign_key(
        "clientotlpendpoint_cluster_id_fkey",
        "clientotlpendpoint",
        "cluster",
        ["cluster_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("additionalnodepool_cluster_id_fkey", "additionalnodepool", type_="foreignkey")
    op.create_foreign_key(
        "additionalnodepool_cluster_id_fkey",
        "additionalnodepool",
        "cluster",
        ["cluster_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("clientnamespace_cluster_id_fkey", "clientnamespace", type_="foreignkey")
    op.create_foreign_key(
        "clientnamespace_cluster_id_fkey",
        "clientnamespace",
        "cluster",
        ["cluster_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column("clusterlock", sa.Column("cluster_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE clusterlock
        SET cluster_id = c.id
        FROM cluster c
        WHERE clusterlock.cluster_name = c.name
        """
    )
    op.execute("DELETE FROM clusterlock WHERE cluster_id IS NULL")
    op.alter_column("clusterlock", "cluster_id", nullable=False)
    op.drop_constraint("clusterlock_pkey", "clusterlock", type_="primary")
    op.drop_constraint("clusterlock_cluster_name_fkey", "clusterlock", type_="foreignkey")
    op.drop_column("clusterlock", "cluster_name")
    op.create_primary_key("clusterlock_pkey", "clusterlock", ["cluster_id"])
    op.create_foreign_key(
        "clusterlock_cluster_id_fkey",
        "clusterlock",
        "cluster",
        ["cluster_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_column("cluster", "kubedownscaler_downscale_period")
    op.drop_column("cluster", "kubedownscaler_upscale_period")


def downgrade() -> None:
    op.add_column("cluster", sa.Column("kubedownscaler_upscale_period", sa.String(), nullable=True))
    op.add_column("cluster", sa.Column("kubedownscaler_downscale_period", sa.String(), nullable=True))

    op.add_column("clusterlock", sa.Column("cluster_name", sa.String(), nullable=True))
    op.execute(
        """
        UPDATE clusterlock
        SET cluster_name = c.name
        FROM cluster c
        WHERE clusterlock.cluster_id = c.id
        """
    )
    op.alter_column("clusterlock", "cluster_name", nullable=False)
    op.drop_constraint("clusterlock_cluster_id_fkey", "clusterlock", type_="foreignkey")
    op.drop_constraint("clusterlock_pkey", "clusterlock", type_="primary")
    op.drop_column("clusterlock", "cluster_id")
    op.create_primary_key("clusterlock_pkey", "clusterlock", ["cluster_name"])
    op.create_foreign_key(
        "clusterlock_cluster_name_fkey",
        "clusterlock",
        "cluster",
        ["cluster_name"],
        ["name"],
    )

    fk_reverts = [
        ("clientnamespace_cluster_id_fkey", "clientnamespace", "cluster", ["cluster_id"], ["id"]),
        ("additionalnodepool_cluster_id_fkey", "additionalnodepool", "cluster", ["cluster_id"], ["id"]),
        ("clientotlpendpoint_cluster_id_fkey", "clientotlpendpoint", "cluster", ["cluster_id"], ["id"]),
        ("userfeature_cluster_id_fkey", "userfeature", "cluster", ["cluster_id"], ["id"]),
        ("releasefeature_feature_id_fkey", "releasefeature", "feature", ["feature_id"], ["id"]),
        ("releasefeature_release_id_fkey", "releasefeature", "release", ["release_id"], ["id"]),
        ("clusterfeature_feature_id_fkey", "clusterfeature", "feature", ["feature_id"], ["id"]),
        ("clusterfeature_cluster_id_fkey", "clusterfeature", "cluster", ["cluster_id"], ["id"]),
    ]
    for name, source, ref, local_cols, remote_cols in fk_reverts:
        op.drop_constraint(name, source, type_="foreignkey")
        op.create_foreign_key(name, source, ref, local_cols, remote_cols)

    op.drop_constraint("feature_name_uc", "feature", type_="unique")
    op.create_unique_constraint("feature_name_type_uc", "feature", ["name", "type"])

    op.drop_constraint("teamswebhook_webhook_id_uc", "teamswebhook", type_="unique")
    op.create_unique_constraint("teamswebhook_webhook_id_key", "teamswebhook", ["webhook_id"])

    op.drop_constraint("cluster_repository_uc", "cluster", type_="unique")
    op.create_unique_constraint("cluster_repository_key", "cluster", ["repository"])

    op.alter_column("feature", "namespaced", nullable=True)
    op.alter_column("feature", "type", nullable=True)
    op.alter_column("release", "reserved_namespaces", existing_type=sa.JSON(), nullable=True)
    op.alter_column("clusterfeature", "enabled", existing_type=sa.Boolean(), nullable=True)
    op.alter_column("cluster", "status", existing_type=sa.String(), nullable=True)
    op.alter_column("clientotlpendpoint", "cluster_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("clientnamespace", "cluster_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("additionalnodepool", "cluster_id", existing_type=sa.Integer(), nullable=True)

    restore_defaults = [
        "vpc_endpoint_service_name",
        "vpc_endpoint_service_ingress_name",
        "cluster_oidc_issuer_url",
        "azure_subnet_name",
        "azure_vnet_name",
        "azure_vnet_resource_group",
        "dns_service_ip",
        "mi_agentpool_object_id",
        "mi_cluster_object_id",
        "account_name",
    ]
    for column in restore_defaults:
        op.alter_column("cluster", column, server_default="")

    op.alter_column("cluster", "account_name", existing_type=sa.String(), nullable=False, server_default="")
