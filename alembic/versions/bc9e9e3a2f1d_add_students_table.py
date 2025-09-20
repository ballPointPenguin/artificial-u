"""add students table

Revision ID: bc9e9e3a2f1d
Revises: 0dc66709d46a
Create Date: 2025-09-20 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "bc9e9e3a2f1d"
down_revision = "0dc66709d46a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("auth0_sub", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("auth0_sub", name="uq_students_auth0_sub"),
    )
    op.create_index("idx_students_email", "students", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_students_email", table_name="students")
    op.drop_table("students")
