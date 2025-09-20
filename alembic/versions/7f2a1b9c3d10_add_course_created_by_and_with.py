"""add course created_by and created_with columns

Revision ID: 7f2a1b9c3d10
Revises: bc9e9e3a2f1d
Create Date: 2025-09-20 13:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7f2a1b9c3d10"
down_revision = "bc9e9e3a2f1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("courses", sa.Column("created_with", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_courses_created_by_students",
        source_table="courses",
        referent_table="students",
        local_cols=["created_by"],
        remote_cols=["id"],
        ondelete=None,
    )


def downgrade() -> None:
    op.drop_constraint("fk_courses_created_by_students", "courses", type_="foreignkey")
    op.drop_column("courses", "created_with")
    op.drop_column("courses", "created_by")
