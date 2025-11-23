"""add image_created_with to professors

Revision ID: 9a7b6c5d4e3f
Revises: 6d8e9f0a1b2c
Create Date: 2025-11-23 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9a7b6c5d4e3f"
down_revision = "6d8e9f0a1b2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add image_created_with column to professors table
    op.add_column("professors", sa.Column("image_created_with", sa.String(), nullable=True))

    # Data migration: Update existing professors with images to set the legacy model
    op.execute(
        """
        UPDATE professors
        SET image_created_with = 'imagen-4.0-generate-001'
        WHERE image_url IS NOT NULL
        """
    )


def downgrade() -> None:
    # Remove image_created_with column from professors table
    op.drop_column("professors", "image_created_with")
