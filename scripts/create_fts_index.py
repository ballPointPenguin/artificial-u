#!/usr/bin/env python
"""
Script to create PostgreSQL full-text search index for the voices table.
Run this after running alembic migrations.
"""

import logging
import os
import sys

from sqlalchemy import create_engine, text

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_fts_index():
    # Get database URL from environment variable
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set.")
        return False

    # Create SQLAlchemy engine
    engine = create_engine(db_url)

    # SQL to create the full-text search index
    sql = text(
        """
    DROP INDEX IF EXISTS idx_voices_text_search;
    CREATE INDEX idx_voices_text_search ON voices USING GIN (to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, '')));
    """
    )

    try:
        # Execute the SQL
        with engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        logger.info("Full-text search index created successfully.")
        return True
    except Exception as e:
        logger.error(f"Error creating full-text search index: {str(e)}")
        return False


if __name__ == "__main__":
    if create_fts_index():
        logger.info("Full-text search index creation completed successfully!")
    else:
        logger.error("Failed to create full-text search index.")
        sys.exit(1)
