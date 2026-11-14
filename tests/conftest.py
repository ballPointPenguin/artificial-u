"""
Global pytest configuration for all tests.
"""

import logging
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from artificial_u.models.database import Base

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_test_database(db_url: str) -> bool:
    """Only databases whose name ends in ``_test`` may be dropped and recreated."""
    return (make_url(db_url).database or "").endswith("_test")


def pytest_sessionstart(session):
    """
    Initialize test environment before tests.

    When the run is selected with exactly ``-m integration``, the test database schema is
    dropped and recreated once up front. Any other marker expression (including
    ``-m "not integration"``) leaves the database alone.
    """
    # Load test environment variables; .env.test wins over anything exported in the shell
    load_dotenv(".env.test", override=True)

    if (session.config.getoption("markexpr") or "").strip() != "integration":
        logger.info("Skipping test database setup (not running integration tests)")
        return

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )
    if not _is_test_database(db_url):
        raise pytest.UsageError(
            "Refusing to reset the schema: DATABASE_URL does not point at a database whose "
            "name ends in '_test'."
        )

    logger.info("Setting up test database for integration tests")
    try:
        engine = create_engine(db_url)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        logger.info("Test database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize test database: {str(e)}")
        logger.warning("Integration tests requiring database may fail!")


@pytest.fixture(scope="session")
def test_db_url():
    """Get the test database URL from environment."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )
