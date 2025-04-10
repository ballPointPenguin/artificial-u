#!/usr/bin/env python3
"""
Database migration script to add new professor fields
"""

import sqlite3
import os
import sys
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(
    description="Migrate database to add new professor fields"
)
parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
args = parser.parse_args()

# Get the database path from environment or use default
db_path = os.environ.get("DATABASE_PATH", "university.db")

# Confirm with user before proceeding unless --yes is specified
if not args.yes:
    print(f"This will modify the database at {db_path}")
    print("Make sure you have a backup before proceeding.")
    response = input("Continue? (y/n): ")

    if response.lower() != "y":
        print("Migration aborted.")
        sys.exit(0)
else:
    print(f"Automatically proceeding with migration on {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the columns already exist
cursor.execute("PRAGMA table_info(professors)")
columns = [column[1] for column in cursor.fetchall()]

# Columns to add
new_columns = [
    ("gender", "VARCHAR"),
    ("accent", "VARCHAR"),
    ("description", "TEXT"),
    ("age", "INTEGER"),
]

# Add each column if it doesn't exist
for column_name, column_type in new_columns:
    if column_name not in columns:
        print(f"Adding column {column_name} ({column_type}) to professors table...")
        cursor.execute(f"ALTER TABLE professors ADD COLUMN {column_name} {column_type}")
        print(f"Column {column_name} added successfully.")
    else:
        print(f"Column {column_name} already exists. Skipping.")

# Commit the changes
conn.commit()
print("Migration completed successfully.")

# Close the connection
conn.close()
