"""Add new consumed_by field to clientnamespace table

Revision ID: e4612c8a30d1
Revises: 1302b37e4b60
Create Date: 2026-02-04 08:20:53.143843
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4612c8a30d1"
down_revision = "1302b37e4b60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clientnamespace",
        sa.Column("consumed_by", sa.String(length=63), nullable=True),
    )

    op.execute(
        """
        UPDATE clientnamespace cn
        SET consumed_by = c.cmdb_appd_id
        FROM cluster c
        WHERE cn.cluster_id = c.id
          AND c.cmdb_appd_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Remove the column
    op.drop_column("clientnamespace", "consumed_by")
