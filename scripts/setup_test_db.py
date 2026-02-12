#!/usr/bin/env python
"""
Script to initialize the test database for integration tests.
This script will create the test database if it does not exist.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on the Python path when executing as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from artificial_u.models.database import Base

# Load test environment variables
load_dotenv(".env.test")

# Get database URL from environment
db_url_str = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
)

db_url = make_url(db_url_str)
db_name = db_url.database

# Connect to the default 'postgres' database to create the test database.
# This is necessary because the test database might not exist yet.
server_url = db_url.set(database="postgres")
creation_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")

with creation_engine.connect() as conn:
    # Check if the database already exists.
    result = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
        {"db_name": db_name},
    )
    db_exists = result.scalar() == 1

    if not db_exists:
        print(f"Database '{db_name}' does not exist. Creating...")
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        print(f"Database '{db_name}' created.")
    else:
        print(f"Database '{db_name}' already exists.")

creation_engine.dispose()

print(f"Initializing tables in test database at {db_url_str}")

# Now connect to the test database to manage tables.
test_db_engine = create_engine(db_url_str)
Base.metadata.drop_all(test_db_engine)
Base.metadata.create_all(test_db_engine)

print("Test database initialized successfully.")
