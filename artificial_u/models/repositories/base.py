"""
Base repository for database operations.
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from artificial_u.models.database import Base


class BaseRepository:
    """
    Base repository class for database operations.
    Provides common functionality for all repositories.
    """

    def __init__(self, db_url: str = None):
        """
        Initialize the repository.

        Args:
            db_url: SQLAlchemy database URL for PostgreSQL connection.
                   If not provided, uses DATABASE_URL environment variable.
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)

        self.db_url = db_url or os.environ.get("DATABASE_URL")

        if not self.db_url:
            raise ValueError("Database URL not provided. Set DATABASE_URL environment variable.")

        self.engine = create_engine(self.db_url)
        self.logger.info(f"Using database URL: {self.db_url}")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: A new SQLAlchemy session
        """
        return Session(self.engine)

    def create_tables(self):
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
