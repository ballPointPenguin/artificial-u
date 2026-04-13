"""add cloned_from to voices

Revision ID: ce5872a4b916
Revises: f5a6b7c8d9e0
Create Date: 2026-04-12 22:42:06.349378

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ce5872a4b916"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("voices", sa.Column("cloned_from", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_voices_cloned_from", "voices", "voices", ["cloned_from"], ["id"], ondelete="SET NULL"
    )
    op.create_index("idx_voices_cloned_from", "voices", ["cloned_from"])


def downgrade() -> None:
    op.drop_index("idx_voices_cloned_from", table_name="voices")
    op.drop_constraint("fk_voices_cloned_from", "voices", type_="foreignkey")
    op.drop_column("voices", "cloned_from")
