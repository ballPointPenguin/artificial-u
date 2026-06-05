"""add language to professors and backfill nulls

Revision ID: a9b8c7d6e5f4
Revises: e9a1c2d3f4b5
Create Date: 2026-06-04 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a9b8c7d6e5f4"
down_revision = "e9a1c2d3f4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column to professors table
    op.add_column("professors", sa.Column("language", sa.String(), nullable=True))

    # Backfill all tables — catches any NULLs created since the 6d8e9f0a1b2c migration
    op.execute("UPDATE professors SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE lectures SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE topics SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE departments SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE faculties SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE courses SET language = 'en' WHERE language IS NULL")


def downgrade() -> None:
    op.drop_column("professors", "language")
