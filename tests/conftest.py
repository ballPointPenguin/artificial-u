"""
Pytest configuration and shared fixtures.
"""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest

from artificial_u.config.settings import get_settings

# Add the project root to Python path (must happen before imports)
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the settings (this will auto-load .env.test in test environments)

# Ensure environment is set up for testing
os.environ["TESTING"] = "true"


# Define helper functions at the top
def is_unit_test():
    """Check if we're running unit tests"""
    return any(arg in sys.argv for arg in ["-m unit", "unit"])


# Only import these if we're not running unit tests or if we're in the unit directory
# This prevents import errors from other modules when running unit tests
if not is_unit_test() or "tests/unit" in os.getcwd():
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError

    from artificial_u.models.database import Base
    from artificial_u.models.repositories import RepositoryFactory
    from artificial_u.system import UniversitySystem
else:
    # Create placeholder classes/variables to avoid import errors
    def create_engine(x):
        return None

    OperationalError = Exception
    RepositoryFactory = object
    Base = object
    UniversitySystem = object


def check_database_exists(db_url: str) -> bool:
    """Check if the test database exists and print helpful message if not."""
    # Skip this check for unit tests
    if is_unit_test():
        return True

    try:
        # Try connecting to the database
        engine = create_engine(db_url)
        conn = engine.connect()
        conn.close()
        return True
    except OperationalError as e:
        if "database" in str(e) and "does not exist" in str(e):
            db_name = db_url.split("/")[-1]
            print("\n\033[91mERROR: Test database not found!\033[0m")
            print(f"The database '{db_name}' does not exist.")
            print("\nTo create the test database, run:")
            print("    python scripts/setup_test_db.py")
            return False
        else:
            print(f"Error connecting to database: {e}")
            return False


@pytest.fixture(scope="session", autouse=True)
def verify_test_environment():
    """
    Verify test environment settings
    """
    settings = get_settings()
    assert settings.testing is True, "Settings should be in test mode"
    assert (
        settings.environment.value == "testing"
    ), "Environment should be set to testing"
    yield


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Provide PostgreSQL URL for tests."""
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # Check if database exists
    if not check_database_exists(db_url):
        pytest.skip("Test database does not exist")

    return db_url


@pytest.fixture(scope="session")
def test_audio_path(tmp_path_factory) -> Path:
    """Provide temporary directory for test audio files."""
    return tmp_path_factory.mktemp("test_audio")


@pytest.fixture
def repository(test_db_url: str) -> Generator[RepositoryFactory, None, None]:
    """Provide a test repository instance with a clean database."""
    # Create a new engine and recreate all tables
    engine = create_engine(test_db_url)

    # Drop all tables and recreate them
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    repo = RepositoryFactory(db_url=test_db_url)
    yield repo

    # Cleanup by dropping tables
    Base.metadata.drop_all(engine)


@pytest.fixture
def mock_system() -> UniversitySystem:
    """Provide a UniversitySystem instance with mocked external dependencies."""
    settings = get_settings()

    return UniversitySystem(
        anthropic_api_key=settings.ANTHROPIC_API_KEY or "mock_anthropic_key",
        elevenlabs_api_key=settings.ELEVENLABS_API_KEY or "mock_elevenlabs_key",
    )
