"""normalize_and_cleanup_features

Revision ID: 5e67ef3550c0
Revises: 44775c618d1f
Create Date: 2026-05-20 09:46:45.990025

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5e67ef3550c0"
down_revision = "44775c618d1f"
branch_labels = None
depends_on = None

EMPTY_JSON_ARRAY = "'[]'::json"


def upgrade() -> None:
    op.execute(
        f"UPDATE feature SET dependencies = {EMPTY_JSON_ARRAY} "
        f"WHERE dependencies IS NULL or dependencies::text = 'null'"
    )
    op.execute(
        f"UPDATE feature SET constraints = {EMPTY_JSON_ARRAY} WHERE constraints IS NULL or constraints::text = 'null'"
    )
    op.alter_column(
        "feature",
        "dependencies",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False,
        existing_server_default=sa.text(EMPTY_JSON_ARRAY),
    )
    op.alter_column(
        "feature",
        "constraints",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False,
        existing_server_default=sa.text(EMPTY_JSON_ARRAY),
    )


def downgrade() -> None:
    op.alter_column(
        "feature",
        "constraints",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True,
        existing_server_default=sa.text(EMPTY_JSON_ARRAY),
    )
    op.alter_column(
        "feature",
        "dependencies",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True,
        existing_server_default=sa.text(EMPTY_JSON_ARRAY),
    )
