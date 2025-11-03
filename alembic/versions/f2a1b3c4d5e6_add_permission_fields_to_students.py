"""Add permission fields to students

Revision ID: f2a1b3c4d5e6
Revises: 48ef6feae5ea
Create Date: 2025-11-02 05:38:40.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a1b3c4d5e6"
down_revision = "48ef6feae5ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns with defaults
    op.add_column(
        "students", sa.Column("role", sa.String(), nullable=False, server_default="viewer")
    )
    op.add_column("students", sa.Column("coins", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "students", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true")
    )


def downgrade() -> None:
    # Remove the columns if rolling back
    op.drop_column("students", "is_active")
    op.drop_column("students", "coins")
    op.drop_column("students", "role")
