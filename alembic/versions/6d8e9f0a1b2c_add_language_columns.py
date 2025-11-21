"""add language columns

Revision ID: 6d8e9f0a1b2c
Revises: 5bb80420d1cc
Create Date: 2025-11-19 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6d8e9f0a1b2c"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column to lectures table
    op.add_column("lectures", sa.Column("language", sa.String(), nullable=True))

    # Add language column to topics table
    op.add_column("topics", sa.Column("language", sa.String(), nullable=True))

    # Add language column to departments table
    op.add_column("departments", sa.Column("language", sa.String(), nullable=True))

    # Add language column to faculties table
    op.add_column("faculties", sa.Column("language", sa.String(), nullable=True))

    # Add language column to courses table
    op.add_column("courses", sa.Column("language", sa.String(), nullable=True))

    # Data migration: Update existing records to set language='en'
    op.execute("UPDATE lectures SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE topics SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE departments SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE faculties SET language = 'en' WHERE language IS NULL")
    op.execute("UPDATE courses SET language = 'en' WHERE language IS NULL")


def downgrade() -> None:
    # Remove language column from courses table
    op.drop_column("courses", "language")

    # Remove language column from faculties table
    op.drop_column("faculties", "language")

    # Remove language column from departments table
    op.drop_column("departments", "language")

    # Remove language column from topics table
    op.drop_column("topics", "language")

    # Remove language column from lectures table
    op.drop_column("lectures", "language")
