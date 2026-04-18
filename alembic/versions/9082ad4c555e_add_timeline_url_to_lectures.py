"""Add timeline_url to lectures

Revision ID: 9082ad4c555e
Revises: ce5872a4b916
Create Date: 2026-04-18 01:22:00.056681

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9082ad4c555e"
down_revision = "ce5872a4b916"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lectures", sa.Column("timeline_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("lectures", "timeline_url")
