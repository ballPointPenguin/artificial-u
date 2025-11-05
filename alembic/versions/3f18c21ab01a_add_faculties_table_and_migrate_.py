"""add_faculties_table_and_migrate_departments

Revision ID: 3f18c21ab01a
Revises: f2a1b3c4d5e6
Create Date: 2025-11-05 06:52:58.519314

"""

import sqlalchemy as sa
from sqlalchemy import text

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

    # Migrate existing faculty string values to faculty records
    # Get connection for data migration
    conn = op.get_bind()

    # Get distinct faculty names from departments
    result = conn.execute(
        text("SELECT DISTINCT faculty FROM departments WHERE faculty IS NOT NULL")
    )
    faculty_names = [row[0] for row in result]

    # Create faculty records and build mapping
    faculty_id_map = {}
    for faculty_name in faculty_names:
        if faculty_name:  # Skip None/empty values
            # Insert faculty and get its ID
            result = conn.execute(
                text(
                    """
                    INSERT INTO faculties (name, description, created_at, updated_at)
                    VALUES (:name, :description, NOW(), NOW())
                    RETURNING id
                """
                ),
                {"name": faculty_name, "description": f"The {faculty_name} faculty."},
            )
            faculty_id = result.scalar()
            faculty_id_map[faculty_name] = faculty_id

    # Update departments with faculty_id based on faculty name
    for faculty_name, faculty_id in faculty_id_map.items():
        conn.execute(
            text("UPDATE departments SET faculty_id = :faculty_id WHERE faculty = :faculty_name"),
            {"faculty_id": faculty_id, "faculty_name": faculty_name},
        )

    # Drop the old faculty string column
    op.drop_column("departments", "faculty")


def downgrade() -> None:
    # Add back the faculty string column
    op.add_column("departments", sa.Column("faculty", sa.String(), nullable=True))

    # Migrate faculty_id back to faculty string
    conn = op.get_bind()
    result = conn.execute(
        text(
            """
        SELECT d.id, f.name
        FROM departments d
        JOIN faculties f ON d.faculty_id = f.id
    """
        )
    )

    for dept_id, faculty_name in result:
        conn.execute(
            text("UPDATE departments SET faculty = :faculty_name WHERE id = :dept_id"),
            {"faculty_name": faculty_name, "dept_id": dept_id},
        )

    # Drop foreign key and faculty_id column
    op.drop_constraint("fk_departments_faculty_id", "departments", type_="foreignkey")
    op.drop_column("departments", "faculty_id")

    # Drop faculties table
    op.drop_table("faculties")
