#!/usr/bin/env python3
"""
Script to create the test database for running integration tests.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv


def create_test_database():
    """Create the test database if it doesn't exist."""
    # Load test environment variables
    load_dotenv(".env.test")

    # Get connection info but ensure we create the artificial_u_test database
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )
    print(f"Database URL from environment: {db_url}")

    # Parse the connection string but force the db_name to artificial_u_test
    if "postgresql://" in db_url:
        parts = db_url.replace("postgresql://", "").split("/")
        credentials = parts[0].split("@")
        user_pass = credentials[0].split(":")
        host_port = credentials[1].split(":")

        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432

        # Always use the test database name
        db_name = "artificial_u_test"

        print(f"Connection info: host={host}, port={port}, user={user}")
        print(f"Will create database: {db_name}")
    else:
        print(f"Invalid database URL format: {db_url}")
        sys.exit(1)

    # Connect to default postgres database to create our test database
    try:
        print(f"Connecting to PostgreSQL server to create test database '{db_name}'...")
        # Connect to the postgres database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname="postgres",  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()

        if not exists:
            print(f"Creating test database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Test database '{db_name}' created successfully.")
        else:
            print(f"Test database '{db_name}' already exists.")

        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"Error setting up test database: {e}")
        return False


if __name__ == "__main__":
    success = create_test_database()
    sys.exit(0 if success else 1)
