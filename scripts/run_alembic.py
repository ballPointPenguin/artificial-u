#!/usr/bin/env python3
"""
Script to run Alembic commands within the project environment.
This ensures that the artificial_u module is available when running migrations.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Change to the project root directory
    os.chdir(project_root)

    # Get the command line arguments (everything after the script name)
    args = sys.argv[1:]

    if not args:
        print("Usage: python scripts/run_alembic.py <alembic_command> [options]")
        print("Example: python scripts/run_alembic.py upgrade head")
        print("Example: python scripts/run_alembic.py revision --autogenerate -m 'Add new table'")
        sys.exit(1)

    # Build the alembic command
    alembic_cmd = ["alembic"] + args

    # Run the command
    try:
        result = subprocess.run(alembic_cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Error running alembic command: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: alembic command not found. Make sure the project environment is set up.")
        print("Run: uv sync, then invoke this script with 'uv run python scripts/run_alembic.py'")
        sys.exit(1)


if __name__ == "__main__":
    main()
