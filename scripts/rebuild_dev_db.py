#!/usr/bin/env python3
"""
Reset the local development database: drop it, recreate it, and apply all migrations.

Every row is lost. The Alembic migration files are not touched; the schema is rebuilt by
running the existing migrations from the first to the latest. Run `scripts/seed_data.py`
afterwards to restore the default faculties.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent

# Hosts that can only be a developer's own database (docker compose exposes "postgres")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "postgres"}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Drop, recreate and migrate the dev database")
    parser.add_argument("--db-url", help="PostgreSQL connection URL (default: DATABASE_URL)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow a database that is not on this machine (never use for production)",
    )
    return parser.parse_args()


def recreate_database(url: URL) -> bool:
    """Drop the database if it exists, then create it empty."""
    db_name = url.database
    quoted_name = '"' + db_name.replace('"', '""') + '"'

    try:
        # DROP/CREATE DATABASE cannot run inside a transaction or against the target itself
        engine = sqlalchemy.create_engine(
            url.set(database="postgres"), isolation_level="AUTOCOMMIT"
        )
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
            ).scalar()

            if exists:
                logger.info(f"Dropping database {db_name}")
                conn.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname = :name AND pid <> pg_backend_pid()"
                    ),
                    {"name": db_name},
                )
                conn.execute(text(f"DROP DATABASE {quoted_name}"))
            else:
                logger.info(f"Database {db_name} does not exist, nothing to drop")

            logger.info(f"Creating database {db_name}")
            conn.execute(text(f"CREATE DATABASE {quoted_name}"))
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Error recreating database: {e}")
        return False


def apply_migrations(url: URL) -> bool:
    """Apply every Alembic migration to the freshly created database."""
    try:
        logger.info("Applying migrations")
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root,
            env={**os.environ, "DATABASE_URL": url.render_as_string(hide_password=False)},
        )
        logger.info("Migrations applied")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error applying migrations: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("alembic not found; run this script with 'uv run python'")
        return False


def main():
    load_dotenv()
    args = parse_args()

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("PostgreSQL connection URL not provided. Set DATABASE_URL or use --db-url")
        sys.exit(1)

    url = make_url(db_url)
    if not url.database:
        logger.error("The database URL does not name a database")
        sys.exit(1)
    if url.host not in LOCAL_HOSTS and not args.allow_remote:
        logger.error(
            f"Refusing to drop a database on '{url.host}'. This script is for local "
            "development databases; pass --allow-remote if you really mean it."
        )
        sys.exit(1)

    if not args.yes:
        print("\n*** WARNING: This will drop and recreate your development database ***")
        print(f"Database: {url.render_as_string(hide_password=True)}")
        print("All data will be lost. Migration files are left as they are.")
        if input("\nContinue? (y/n): ").lower() != "y":
            print("Operation cancelled.")
            sys.exit(0)

    if not recreate_database(url):
        sys.exit(1)
    if not apply_migrations(url):
        sys.exit(1)

    logger.info("Development database rebuilt. Run scripts/seed_data.py to seed faculties.")


if __name__ == "__main__":
    main()
