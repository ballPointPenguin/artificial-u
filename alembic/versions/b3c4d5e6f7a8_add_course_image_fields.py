"""add course image_url and image_created_with

Revision ID: b3c4d5e6f7a8
Revises: 9082ad4c555e
Create Date: 2026-04-20 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "b3c4d5e6f7a8"
down_revision = "9082ad4c555e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column("courses", sa.Column("image_created_with", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "image_created_with")
    op.drop_column("courses", "image_url")
