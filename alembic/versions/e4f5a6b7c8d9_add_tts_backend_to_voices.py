"""Add tts_backend and external_id columns to voices table

Adds tts_backend (default 'elevenlabs') and external_id columns to support
multiple TTS providers. Makes el_voice_id nullable for non-ElevenLabs voices.
Backfills tts_backend='elevenlabs' and external_id=el_voice_id for existing rows.

Revision ID: e4f5a6b7c8d9
Revises: d1e2f3a4b5c6
Create Date: 2026-03-31 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e4f5a6b7c8d9"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add tts_backend column with server default so existing rows get backfilled
    op.add_column(
        "voices",
        sa.Column(
            "tts_backend",
            sa.String(50),
            nullable=False,
            server_default="elevenlabs",
        ),
    )

    # 2. Add external_id column (nullable, will be populated by backfill)
    op.add_column(
        "voices",
        sa.Column("external_id", sa.String(), nullable=True),
    )

    # 3. Backfill external_id = el_voice_id for all existing (ElevenLabs) voices
    op.execute("UPDATE voices SET external_id = el_voice_id WHERE el_voice_id IS NOT NULL")

    # 4. Make el_voice_id nullable (was NOT NULL) for non-ElevenLabs voices
    op.alter_column("voices", "el_voice_id", existing_type=sa.String(), nullable=True)

    # 5. Add index on tts_backend for filtering
    op.create_index("idx_voices_tts_backend", "voices", ["tts_backend"])

    # 6. Add partial unique index on (tts_backend, external_id) where external_id is not null
    op.execute(
        "CREATE UNIQUE INDEX uq_voices_backend_external_id "
        "ON voices (tts_backend, external_id) "
        "WHERE external_id IS NOT NULL"
    )


def downgrade() -> None:
    # Drop the partial unique index
    op.execute("DROP INDEX IF EXISTS uq_voices_backend_external_id")

    # Drop the tts_backend index
    op.drop_index("idx_voices_tts_backend", table_name="voices")

    # Restore el_voice_id to NOT NULL (backfill any NULLs first)
    op.execute(
        "UPDATE voices SET el_voice_id = external_id "
        "WHERE el_voice_id IS NULL AND external_id IS NOT NULL"
    )
    op.alter_column("voices", "el_voice_id", existing_type=sa.String(), nullable=False)

    # Drop the new columns
    op.drop_column("voices", "external_id")
    op.drop_column("voices", "tts_backend")
