import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from artificial_u.api.app import app, create_application
from artificial_u.models.database import Base, Repository


def pytest_runtest_setup(item):
    """Skip tests if database is not available."""
    if "/api/" in str(item.fspath):
        if not is_db_available():
            pytest.skip("Database not available for API tests")


def is_db_available():
    """Check if the database is available."""
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )

    try:
        # Try to connect to the database
        engine = create_engine(db_url)
        with engine.connect():
            return True
    except OperationalError:
        return False
    except Exception:
        return False


@pytest.fixture(scope="session")
def test_db_url():
    """Get the test database URL from environment."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def test_app():
    """Create a fresh instance of the FastAPI application for testing."""
    return create_application()


@pytest.fixture
def test_repository(test_db_url):
    """Create a repository for database operations in tests."""
    return Repository(db_url=test_db_url)


@pytest.fixture(scope="function")
def setup_test_db(test_db_url):
    """Set up a clean test database for API tests."""
    # Setup the database with minimal schema
    engine = create_engine(test_db_url)

    # Truncate all tables instead of dropping and recreating them
    with engine.connect() as conn:
        with conn.begin():
            # Get a list of all tables
            tables = Base.metadata.tables.keys()

            # Disable foreign key constraints
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

            # Truncate each table
            for table in tables:
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

            # Re-enable constraints
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

    yield

    # Clean up after test
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            for table in Base.metadata.tables.keys():
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
