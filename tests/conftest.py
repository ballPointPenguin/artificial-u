"""
Global pytest configuration for all tests.
"""

import logging
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine

from artificial_u.models.database import Base

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "asyncio: mark test as an async test")


def pytest_sessionstart(session):
    """
    Initialize test environment before tests.

    This is the best place to set up the test database once before all tests run.
    """
    # Load test environment variables
    load_dotenv(".env.test")

    # Check if integration tests will be run
    if session.config.getoption("markexpr") and "integration" in session.config.getoption(
        "markexpr"
    ):
        logger.info("Setting up test database for integration tests")

        # Get database URL from environment
        db_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
        )

        try:
            # Create engine and tables
            engine = create_engine(db_url)
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            logger.info("Test database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize test database: {str(e)}")
            logger.warning("Integration tests requiring database may fail!")
    else:
        logger.info("Skipping test database setup (not running integration tests)")


@pytest.fixture(scope="session")
def test_db_url():
    """Get the test database URL from environment."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )
