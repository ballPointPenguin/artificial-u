"""Add featured_items table

Revision ID: c3e5g7i9k1m3
Revises: b2d4f6h8j0l2
Create Date: 2026-02-11 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c3e5g7i9k1m3"
down_revision = "b2d4f6h8j0l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "featured_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="en"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_featured_items_type_language",
        "featured_items",
        ["item_type", "language"],
    )
    op.create_unique_constraint(
        "uq_featured_items_type_id_language",
        "featured_items",
        ["item_type", "item_id", "language"],
    )


def downgrade() -> None:
    op.drop_index("ix_featured_items_type_language", table_name="featured_items")
    op.drop_table("featured_items")
