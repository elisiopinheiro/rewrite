"""Add owner_group field

Revision ID: a90bf054665a
Revises: 4bf4403793c7
Create Date: 2023-01-05 14:55:49.655191

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "a90bf054665a"
down_revision = "4bf4403793c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cluster",
        sa.Column("owner_group", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cluster", "owner_group")
