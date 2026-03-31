"""Add tts_backend column to professors table

Allows per-professor TTS backend override. When NULL, the system default
(from settings.tts_backend) is used.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-03-31 00:00:01.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "professors",
        sa.Column("tts_backend", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("professors", "tts_backend")
