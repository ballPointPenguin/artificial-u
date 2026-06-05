"""Add course_connections table for symmetric course links.

Revision ID: 576995cc0e6d
Revises: d7e8f9a0b1c2
Create Date: 2026-06-04 21:52:17.334788

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "576995cc0e6d"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_connections",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("connected_course_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connected_course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("course_id", "connected_course_id"),
        sa.CheckConstraint(
            "course_id < connected_course_id",
            name="ck_course_connections_ordering",
        ),
    )
    op.create_index(
        "idx_course_connections_connected_course_id",
        "course_connections",
        ["connected_course_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_course_connections_connected_course_id",
        table_name="course_connections",
    )
    op.drop_table("course_connections")
