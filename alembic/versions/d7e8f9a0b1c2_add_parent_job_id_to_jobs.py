"""add parent_job_id to jobs

Revision ID: d7e8f9a0b1c2
Revises: c4d5e6f7a8b9
Create Date: 2026-04-29

"""

import sqlalchemy as sa

from alembic import op

revision = "d7e8f9a0b1c2"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("parent_job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=True),
    )
    op.create_index("idx_jobs_parent_job_id", "jobs", ["parent_job_id"])


def downgrade() -> None:
    op.drop_index("idx_jobs_parent_job_id", table_name="jobs")
    op.drop_column("jobs", "parent_job_id")
