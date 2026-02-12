"""Add duration to lectures

Revision ID: b2d4f6h8j0l2
Revises: a1c3e5g7i9k1
Create Date: 2026-02-10 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2d4f6h8j0l2"
down_revision = "a1c3e5g7i9k1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lectures", sa.Column("duration", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lectures", "duration")
