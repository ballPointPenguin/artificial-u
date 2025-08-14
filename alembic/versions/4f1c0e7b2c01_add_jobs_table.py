"""
add jobs table

Revision ID: 4f1c0e7b2c01
Revises: 4a88cb5f6566_add_unique_constraint_topic_course_week_
Create Date: 2025-08-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f1c0e7b2c01"
down_revision: Union[str, None] = "4a88cb5f6566"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "run_after",
            sa.TIMESTAMP(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_jobs_status_priority_runafter",
        "jobs",
        [
            "status",
            sa.text("priority DESC"),
            "run_after",
        ],
    )
    op.create_index(
        "idx_jobs_status_updatedat",
        "jobs",
        ["status", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_jobs_status_updatedat", table_name="jobs")
    op.drop_index("idx_jobs_status_priority_runafter", table_name="jobs")
    op.drop_table("jobs")
