"""merge faculties and word_count migrations

Revision ID: 5bb80420d1cc
Revises: 3f18c21ab01a, 7c9d3a52b6f4
Create Date: 2025-11-07 14:19:50.085959

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5bb80420d1cc"
down_revision = ("3f18c21ab01a", "7c9d3a52b6f4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
