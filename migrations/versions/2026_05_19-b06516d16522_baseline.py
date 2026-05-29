"""Legacy-compatible baseline schema.

Revision ID: b06516d16522
Revises:
Create Date: 2026-05-19 10:00:00.000000

"""

from alembic import op

from app.models.base import Base

# revision identifiers, used by Alembic.
revision = "b06516d16522"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
