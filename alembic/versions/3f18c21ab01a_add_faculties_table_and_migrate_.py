"""add_faculties_table_and_migrate_departments

Revision ID: 3f18c21ab01a
Revises: f2a1b3c4d5e6
Create Date: 2025-11-05 06:52:58.519314

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3f18c21ab01a"
down_revision = "f2a1b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create faculties table
    op.create_table(
        "faculties",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Add faculty_id column to departments (nullable initially)
    op.add_column("departments", sa.Column("faculty_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_departments_faculty_id",
        "departments",
        "faculties",
        ["faculty_id"],
        ["id"],
    )

    # Drop the old faculty string column (no data migration)
    op.drop_column("departments", "faculty")


def downgrade() -> None:
    # Add back the faculty string column
    op.add_column("departments", sa.Column("faculty", sa.String(), nullable=True))

    # Drop foreign key and faculty_id column (no data backfill)
    op.drop_constraint("fk_departments_faculty_id", "departments", type_="foreignkey")
    op.drop_column("departments", "faculty_id")

    # Drop faculties table
    op.drop_table("faculties")
