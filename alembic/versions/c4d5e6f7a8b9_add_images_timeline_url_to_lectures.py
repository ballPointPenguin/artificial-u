"""Add images_timeline_url to lectures

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-23 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lectures", sa.Column("images_timeline_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("lectures", "images_timeline_url")
