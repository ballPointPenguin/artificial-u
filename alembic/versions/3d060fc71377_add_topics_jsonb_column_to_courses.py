"""add topics jsonb column to courses

Revision ID: 3d060fc71377
Revises: 95816da14c74
Create Date: 2025-04-30 08:08:07.891507

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "3d060fc71377"
down_revision = "95816da14c74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("courses", "topics")
