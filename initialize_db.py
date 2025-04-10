#!/usr/bin/env python3
"""
Initialize PostgreSQL database for ArtificialU.
"""

import os
import sys
import logging
import argparse
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

    # Initialize database
    try:
        # Create engine
        engine = sqlalchemy.create_engine(db_url)

        # Read migration SQL file
        migration_file = os.path.join("migrations", "00001_initial_schema.sql")

        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            sys.exit(1)

        with open(migration_file, "r") as f:
            sql_script = f.read()

        # Execute SQL script
        logger.info("Executing initial schema migration...")

        with engine.connect() as conn:
            conn.execute(text(sql_script))
            conn.commit()

        logger.info("Database initialized successfully!")

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
