#!/usr/bin/env python
"""
Script to initialize the test database for integration tests.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from artificial_u.models.database import Base

# Load test environment variables
load_dotenv(".env.test")

# Get database URL from environment
db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
)

print(f"Initializing test database at {db_url}")

# Create engine and tables
engine = create_engine(db_url)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

print("Test database initialized successfully.")
