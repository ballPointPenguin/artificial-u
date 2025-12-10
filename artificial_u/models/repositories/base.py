"""
Base repository for database operations.
"""

import logging
import os
from typing import Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from artificial_u.models.database import Base
from artificial_u.models.engine import get_engine


class BaseRepository:
    """
    Base repository class for database operations.
    Provides common functionality for all repositories.

    Uses a shared engine singleton to prevent connection pool explosion.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        engine: Optional[Engine] = None,
    ):
        """
        Initialize the repository.

        Args:
            db_url: SQLAlchemy database URL for PostgreSQL connection.
                   If not provided, uses DATABASE_URL environment variable.
                   Ignored if engine is provided.
            engine: Optional shared SQLAlchemy engine. If not provided,
                   uses the shared engine singleton from get_engine().
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)

        if engine is not None:
            # Use provided shared engine
            self.engine = engine
            self.db_url = str(engine.url)
        else:
            # Fall back to getting/creating shared engine
            self.db_url = db_url or os.environ.get("DATABASE_URL")

            if not self.db_url:
                raise ValueError(
                    "Database URL not provided. Set DATABASE_URL environment variable."
                )

            # Use the shared engine singleton instead of creating a new one
            self.engine = get_engine(self.db_url)

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

    def dispose_engine(self):
        """
        Dispose of the database engine and close all connections.

        Note: This is now a no-op for individual repositories since they
        share the singleton engine. Use engine.dispose_engine() directly
        if you need to dispose the shared engine.
        """
        # No-op - we don't dispose the shared singleton from individual repos
        self.logger.debug("dispose_engine() called on repository - no-op for shared engine")
