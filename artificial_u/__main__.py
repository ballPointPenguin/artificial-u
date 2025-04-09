"""
Main entry point for ArtificialU.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import CLI
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli import cli

if __name__ == "__main__":
    # Check for required environment variables
    missing_vars = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing_vars.append("ANTHROPIC_API_KEY")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        missing_vars.append("ELEVENLABS_API_KEY")

    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print(
            "\
Please set these in a .env file or environment variables before running."
        )
        print("You can copy .env.example to .env and fill in the values.")
        sys.exit(1)

    # Run CLI
    cli()
