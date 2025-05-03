#!/usr/bin/env python3
"""
Script to create and set up the test database for running integration tests.
Applies Alembic migrations to ensure the database schema is up to date.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get the project root directory
project_root = Path(__file__).parent.parent

# Force test environment
os.environ["TESTING"] = "true"
os.environ["ENV_FILE"] = str(project_root / ".env.test")

# Load test environment variables first
load_dotenv(str(project_root / ".env.test"), override=True)

# Add the project root to Python path
sys.path.insert(0, str(project_root))

# Import settings (will automatically load .env.test)
from artificial_u.config.settings import get_settings


def get_database_name(db_url):
    """Extract database name from connection URL."""
    if "postgresql://" in db_url:
        return db_url.split("/")[-1]
    return None


def setup_test_database():
    """Create and set up the test database with Alembic migrations."""
    # Get settings for the test environment
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")

    # Get database URL from settings
    db_url = settings.DATABASE_URL
    logger.info(f"Using database URL: {db_url}")

    if not db_url:
        logger.error("DATABASE_URL not found in test settings")
        return False

    # Verify this is a test database
    db_name = get_database_name(db_url)
    if not db_name or "test" not in db_name.lower():
        logger.error(
            f"Database name '{db_name}' does not contain 'test'. This script should only be used with test databases."
        )
        logger.error(
            "Please check your .env.test file and ensure DATABASE_URL points to a test database."
        )
        return False

    # Drop and recreate database
    if not drop_database(db_url):
        return False

    # Apply migrations
    if not apply_migrations():
        return False

    logger.info("Test database setup completed successfully!")
    return True


def drop_database(db_url):
    """Drop the database if it exists and create a new one."""
    db_name = get_database_name(db_url)
    if not db_name:
        logger.error(f"Invalid database URL format: {db_url}")
        return False

    # Create a connection URL to postgres database
    postgres_url = db_url.rsplit("/", 1)[0] + "/postgres"

    try:
        # Connect to postgres database
        engine = sqlalchemy.create_engine(postgres_url)
        with engine.connect() as conn:
            # Don't automatically commit transactions
            conn.execution_options(isolation_level="AUTOCOMMIT")

            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            exists = result.scalar() == 1

            if exists:
                logger.info(f"Dropping database {db_name}")
                # Make sure there are no active connections
                conn.execute(
                    text(
                        f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                        f"FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_name}' "
                        f"AND pid <> pg_backend_pid()"
                    )
                )
                conn.execute(text(f"DROP DATABASE {db_name}"))
                logger.info(f"Database {db_name} dropped successfully")
            else:
                logger.info(f"Database {db_name} does not exist, nothing to drop")

            # Create the database
            logger.info(f"Creating database {db_name}")
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            logger.info(f"Database {db_name} created successfully")

        return True
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        return False


def apply_migrations():
    """Apply Alembic migrations to the test database."""
    try:
        logger.info("Applying Alembic migrations")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Migrations applied successfully: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error applying migrations: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error applying migrations: {str(e)}")
        return False


if __name__ == "__main__":
    success = setup_test_database()
    sys.exit(0 if success else 1)
