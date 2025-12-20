"""add preferences table

Revision ID: a1c3e5g7i9k1
Revises: pxfhh15d6yq2
Create Date: 2025-12-19 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c3e5g7i9k1"
down_revision = "pxfhh15d6yq2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create preferences table
    op.create_table(
        "preferences",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name="fk_preferences_student_id"),
    )

    # Create index for global preferences - unique scope when is_global is true
    op.execute(
        """
        CREATE UNIQUE INDEX idx_preferences_global_scope
        ON preferences (scope)
        WHERE is_global = true
        """
    )

    # Create index for user preferences - unique student_id + scope when is_global is false
    op.execute(
        """
        CREATE UNIQUE INDEX idx_preferences_student_scope
        ON preferences (student_id, scope)
        WHERE is_global = false
        """
    )

    # Create index for efficient lookup of global preferences
    op.create_index("idx_preferences_is_global", "preferences", ["is_global"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_preferences_is_global", table_name="preferences")
    op.execute("DROP INDEX IF EXISTS idx_preferences_student_scope")
    op.execute("DROP INDEX IF EXISTS idx_preferences_global_scope")

    # Drop table
    op.drop_table("preferences")
