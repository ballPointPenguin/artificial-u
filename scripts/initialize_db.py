#!/usr/bin/env python3
"""
Initialize PostgreSQL database for ArtificialU.
"""

import os
import sys
import logging
import argparse
import subprocess
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize PostgreSQL database for ArtificialU"
    )
    parser.add_argument("--db-url", help="PostgreSQL connection URL")
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    return parser.parse_args()


def create_database_if_not_exists(db_url, logger):
    """Create the database if it doesn't exist."""
    # Parse the connection string to get database name
    if "postgresql://" in db_url:
        # Get the database name from the URL
        db_name = db_url.split("/")[-1]
        # Create a connection URL without the database name
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

                if not exists:
                    logger.info(f"Creating database {db_name}")
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"Database {db_name} created successfully")
                else:
                    logger.info(f"Database {db_name} already exists")

            return True
        except Exception as e:
            logger.error(f"Error creating database: {str(e)}")
            return False
    else:
        logger.error(f"Invalid database URL format: {db_url}")
        return False


def run_alembic_migrations(db_url, logger):
    """Run Alembic migrations."""
    try:
        # Set database URL for Alembic
        os.environ["DATABASE_URL"] = db_url

        # Check if alembic directory exists
        if not os.path.exists("alembic"):
            logger.info("Initializing Alembic")
            subprocess.run(["alembic", "init", "alembic"], check=True)
            logger.info("Alembic initialized successfully")

        # Run migrations
        logger.info("Running Alembic migrations")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running migrations: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running migrations: {str(e)}")
        return False


def main():
    """Main initialization function."""
    # Load environment variables
    load_dotenv()

    # Set up logging
    logger = setup_logging()

    # Parse arguments
    args = parse_args()

    # Get database URL
    db_url = args.db_url or os.environ.get("DATABASE_URL")

    if not db_url:
        logger.error(
            "PostgreSQL connection URL not provided. Set DATABASE_URL or use --db-url"
        )
        sys.exit(1)

    # Confirm with user
    if not args.yes:
        print(f"This will initialize the PostgreSQL database at {db_url}")
        print("WARNING: This might overwrite existing data if tables already exist.")
        response = input("Continue? (y/n): ")

        if response.lower() != "y":
            print("Initialization aborted.")
            sys.exit(0)

    # Create database if it doesn't exist
    if not create_database_if_not_exists(db_url, logger):
        sys.exit(1)

    # Run migrations
    if not run_alembic_migrations(db_url, logger):
        sys.exit(1)

    logger.info("Database initialized successfully!")


if __name__ == "__main__":
    main()
