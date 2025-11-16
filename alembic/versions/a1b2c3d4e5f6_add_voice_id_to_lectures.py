"""add voice_id to lectures

Revision ID: a1b2c3d4e5f6
Revises: 5bb80420d1cc
Create Date: 2025-11-16 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "5bb80420d1cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the voice_id column
    op.add_column(
        "lectures",
        sa.Column("voice_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lectures_voice_id",
        "lectures",
        "voices",
        ["voice_id"],
        ["id"],
    )

    # Backfill voice_id for existing lectures based on their course's professor's voice
    # This SQL query updates lectures to use the voice_id from the professor assigned to the course
    connection = op.get_bind()
    connection.execute(
        text(
            """
            UPDATE lectures
            SET voice_id = professors.voice_id
            FROM courses
            JOIN professors ON courses.professor_id = professors.id
            WHERE lectures.course_id = courses.id
              AND professors.voice_id IS NOT NULL
              AND lectures.audio_url IS NOT NULL
        """
        )
    )


def downgrade() -> None:
    op.drop_constraint("fk_lectures_voice_id", "lectures", type_="foreignkey")
    op.drop_column("lectures", "voice_id")
