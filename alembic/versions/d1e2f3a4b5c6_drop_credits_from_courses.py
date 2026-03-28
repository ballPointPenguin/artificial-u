"""Drop credits column from courses table

Revision ID: d1e2f3a4b5c6
Revises: c3e5g7i9k1m3
Create Date: 2026-03-28 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c3e5g7i9k1m3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("courses", "credits")


def downgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("credits", sa.Integer(), nullable=True, server_default="3"),
    )
