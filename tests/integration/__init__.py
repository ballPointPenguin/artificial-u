"""
Integration tests package for the ArtificialU project.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


# Create a fixture that checks database connectivity
@pytest.fixture(scope="session")
def db_available():
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


# Create an autouse fixture that will skip tests marked with integration if the
# database is not available
@pytest.fixture(autouse=True)
def skip_if_no_db(request, db_available):
    """Skip tests that require a database if the database is not available."""
    if request.node.get_closest_marker("integration") and not db_available:
        pytest.skip("Database not available")
