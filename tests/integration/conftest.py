"""
Fixtures for integration tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from artificial_u.config import get_settings
from artificial_u.models.database import Base


@pytest.fixture(scope="session", autouse=True)
def ensure_schema():
    """
    Ensure the database schema exists for integration tests.

    This fixture runs once per test session and creates tables if they don't exist,
    without dropping existing tables. This ensures the schema is ready for tests
    without destroying data between test runs.
    """
    # Get database settings from test environment
    settings = get_settings()

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Create tables that don't exist yet
    Base.metadata.create_all(engine)

    yield


@pytest.fixture(scope="function", autouse=True)
def db_transaction():
    """
    Create a transactional scope around all tests in integration tests.

    This ensures test isolation by rolling back all changes made in the test
    and prevents test data from persisting between test runs.
    """
    # Get database settings from test environment
    settings = get_settings()

    # Create engine and session factory
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)

    # Connect to the database and start a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection
    session = Session(bind=connection)

    # Make session available for test repositories
    from artificial_u.models.repositories.base import BaseRepository

    original_get_session = BaseRepository.get_session

    def patched_get_session(self):
        return session

    # Apply patch
    BaseRepository.get_session = patched_get_session

    # Run the test
    yield

    # Restore original method
    BaseRepository.get_session = original_get_session

    # Rollback the transaction after the test completes
    if transaction.is_active:
        transaction.rollback()

    # Close the session and connection
    session.close()
    connection.close()
