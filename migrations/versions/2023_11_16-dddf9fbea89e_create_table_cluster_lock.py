"""Create table cluster lock

Revision ID: dddf9fbea89e
Revises: 3fe9f3ae2fb6
Create Date: 2023-10-24 12:34:41.432709

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "dddf9fbea89e"
down_revision = "5d5e9ad536ee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("cluster_name_uc", "cluster", ["name"])

    op.create_table(
        "clusterlock",
        sa.Column("cluster_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("owner", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("timeout_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cluster_name"],
            ["cluster.name"],
        ),
        sa.PrimaryKeyConstraint("cluster_name"),
    )


def downgrade() -> None:
    op.drop_table("clusterlock")
    op.drop_constraint("cluster_name_uc", "cluster", type_="unique")
