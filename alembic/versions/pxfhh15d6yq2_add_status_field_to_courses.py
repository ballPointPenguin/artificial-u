"""add_status_field_to_courses

Revision ID: pxfhh15d6yq2
Revises: 3f18c21ab01a
Create Date: 2025-11-25 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "pxfhh15d6yq2"
down_revision = "9a7b6c5d4e3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status column with default 'hidden' for new rows
    # But set existing courses to 'published'
    op.add_column(
        "courses", sa.Column("status", sa.String(), nullable=False, server_default="hidden")
    )

    # Update existing courses to 'published'
    op.execute("UPDATE courses SET status = 'published'")


def downgrade() -> None:
    op.drop_column("courses", "status")
