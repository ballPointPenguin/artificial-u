#!/usr/bin/env python3
"""
Script to create the test database for running integration tests.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv


def setup_test_database():
    """Create and set up the test database."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Load test environment variables from the correct path
    env_path = project_root / ".env.test"
    print(f"Loading environment from: {env_path.absolute()}")

    # First reset any existing environment variables that might be interfering
    if "DATABASE_URL" in os.environ:
        print(f"Clearing existing DATABASE_URL: {os.environ['DATABASE_URL']}")
        del os.environ["DATABASE_URL"]

    # Load the test environment
    load_dotenv(env_path, override=True)

    # Debug: print all environment variables
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if key.startswith("DATABASE") or "TEST" in key:
            print(f"{key}={value}")
    print()

    # Get connection info from .env.test
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        print("Error: DATABASE_URL not found in .env.test")
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

    # Drop the test database if it exists
    drop_db_cmd = [
        "psql",
        "-U",
        db_user,
        "-h",
        "localhost",
        "-c",
        f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE);",
    ]

    try:
        print("Dropping existing database...")
        result = subprocess.run(drop_db_cmd, check=True, capture_output=True, text=True)
        print(f"Dropped existing database: {db_name}")
        print(f"Output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to drop database: {e}")
        print(f"Error output: {e.stderr}")

    # Create the test database
    create_db_cmd = [
        "psql",
        "-U",
        db_user,
        "-h",
        "localhost",
        "-c",
        f"CREATE DATABASE {db_name};",
    ]

    try:
        print("Creating database...")
        result = subprocess.run(
            create_db_cmd, check=True, capture_output=True, text=True
        )
        print(f"Created database: {db_name}")
        print(f"Output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating database: {e}")
        print(f"Error output: {e.stderr}")
        return False

    # Run initialize_db.py with the test database URL
    try:
        print("Running database initialization...")
        script_path = os.path.join(project_root, "scripts", "initialize_db.py")
        result = subprocess.run(
            [sys.executable, script_path, "--db-url", db_url, "--yes"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Test database initialized successfully")
        print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing test database: {e}")
        print(f"Error output: {e.stderr}")
        return False


if __name__ == "__main__":
    success = setup_test_database()
    sys.exit(0 if success else 1)
