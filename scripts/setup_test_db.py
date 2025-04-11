#!/usr/bin/env python3
"""
Script to create the test database for running integration tests.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up test environment
os.environ["TESTING"] = "true"
os.environ["ENV_FILE"] = str(project_root / ".env.test")

# Import settings (will automatically load .env.test)
from artificial_u.config.settings import get_settings


def setup_test_database():
    """Create and set up the test database."""
    # Get settings for the test environment
    settings = get_settings()
    print(f"Environment: {settings.environment}")

    # Get database URL from settings
    db_url = settings.DATABASE_URL
    print(f"Using database URL: {db_url}")

    if not db_url:
        print("Error: DATABASE_URL not found in test settings")
        return False

    # Extract database name and connection details from URL
    db_parts = db_url.split("/")
    db_name = db_parts[-1]

    # Parse connection details for PostgreSQL
    connection_info = db_url.split("//")[1].split("@")[0]
    user_password = connection_info.split(":")
    db_user = user_password[0]
    db_password = user_password[1]

    # Set PostgreSQL password environment variable to avoid prompt
    os.environ["PGPASSWORD"] = db_password

    connection_string = (
        "/".join(db_parts[:-1]) + "/postgres"
    )  # Connect to postgres database for admin operations

    print(f"Setting up test database: {db_name}")
    print(f"Using connection string: {connection_string}")

    try:
        # Drop the database if it exists
        drop_cmd = f"dropdb --if-exists -h {db_url.split('@')[1].split('/')[0]} -U {db_user} {db_name}"
        print(f"Dropping existing database: {drop_cmd}")
        subprocess.run(drop_cmd, shell=True, check=True)

        # Create the database
        create_cmd = (
            f"createdb -h {db_url.split('@')[1].split('/')[0]} -U {db_user} {db_name}"
        )
        print(f"Creating database: {create_cmd}")
        subprocess.run(create_cmd, shell=True, check=True)

        print(f"Successfully created database '{db_name}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating test database: {e}")
        return False


if __name__ == "__main__":
    success = setup_test_database()
    sys.exit(0 if success else 1)
