#!/usr/bin/env python3
"""
Script to create the test database for running integration tests.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv


def setup_test_database():
    """Create and set up the test database."""
    # Load test environment variables
    load_dotenv(".env.test")

    # Get connection info
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )
    print(f"Using database URL: {db_url}")

    # Run initialize_db.py with the test database URL
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "initialize_db.py",
        )
        subprocess.run(
            [sys.executable, script_path, "--db-url", db_url, "--yes"],
            check=True,
        )
        print("Test database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing test database: {e}")
        return False


if __name__ == "__main__":
    success = setup_test_database()
    sys.exit(0 if success else 1)
