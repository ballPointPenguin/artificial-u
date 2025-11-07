"""Add word_count to lectures

Revision ID: 7c9d3a52b6f4
Revises: f2a1b3c4d5e6
Create Date: 2025-11-07 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7c9d3a52b6f4"
down_revision = "f2a1b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lectures", sa.Column("word_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lectures", "word_count")
