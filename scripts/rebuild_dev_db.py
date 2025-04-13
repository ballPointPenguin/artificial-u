#!/usr/bin/env python3
"""
Script to rebuild the development database and recreate initial Alembic migration.
Only for use in development/greenfield phase.
"""

import argparse
import glob
import logging
import os
import subprocess
import sys
from pathlib import Path

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get the project root directory
project_root = Path(__file__).parent.parent
versions_dir = project_root / "alembic" / "versions"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Rebuild development database and recreate initial migration"
    )
    parser.add_argument("--db-url", help="PostgreSQL connection URL")
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    return parser.parse_args()


def get_database_name(db_url):
    """Extract database name from connection URL."""
    if "postgresql://" in db_url:
        return db_url.split("/")[-1]
    return None


def drop_database(db_url, logger):
    """Drop the database if it exists."""
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
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
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


def delete_migration_files(logger):
    """Delete all migration files in the alembic/versions directory."""
    try:
        migration_files = glob.glob(str(versions_dir / "*.py"))
        if migration_files:
            for file in migration_files:
                logger.info(f"Deleting migration file: {file}")
                os.remove(file)
            logger.info("All migration files deleted successfully")
        else:
            logger.info("No migration files to delete")
        return True
    except Exception as e:
        logger.error(f"Error deleting migration files: {str(e)}")
        return False


def create_initial_migration(logger):
    """Create a fresh initial migration."""
    try:
        logger.info("Creating fresh initial migration")
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Migration created successfully: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating migration: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating migration: {str(e)}")
        return False


def apply_migration(logger):
    """Apply the new migration."""
    try:
        logger.info("Applying migration")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Migration applied successfully: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error applying migration: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error applying migration: {str(e)}")
        return False


def create_fts_index(logger):
    """Run the FTS index creation script."""
    try:
        logger.info("Creating FTS index")
        # Use the existing script
        result = subprocess.run(
            ["python", str(project_root / "scripts" / "create_fts_index.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"FTS index created successfully: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating FTS index: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating FTS index: {str(e)}")
        return False


def main():
    """Main function to rebuild the database and migrations."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_args()

    # Get database URL
    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error(
            "PostgreSQL connection URL not provided. Set DATABASE_URL or use --db-url"
        )
        sys.exit(1)

    # Show warning and confirm
    if not args.yes:
        print("\n*** WARNING: This will completely reset your development database ***")
        print(f"Database: {db_url}")
        print(
            "All data will be lost, and Alembic migrations will be recreated from scratch."
        )
        print("This should ONLY be used during greenfield development.")
        response = input("\nContinue? (y/n): ")

        if response.lower() != "y":
            print("Operation cancelled.")
            sys.exit(0)

    # Drop and recreate database
    if not drop_database(db_url, logger):
        sys.exit(1)

    # Delete migration files
    if not delete_migration_files(logger):
        sys.exit(1)

    # Create fresh migration
    if not create_initial_migration(logger):
        sys.exit(1)

    # Apply migration
    if not apply_migration(logger):
        sys.exit(1)

    # Create FTS index
    if not create_fts_index(logger):
        sys.exit(1)

    logger.info("Development database rebuild completed successfully!")


if __name__ == "__main__":
    main()
