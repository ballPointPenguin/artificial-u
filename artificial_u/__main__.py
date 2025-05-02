"""
Main entry point for ArtificialU.
"""

import os
import sys

from dotenv import load_dotenv

from artificial_u.cli import cli

# Load environment variables from .env file
load_dotenv()

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_api_keys():
    """Check if required API keys are set in environment variables."""
    # Check for required environment variables
    missing_vars = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing_vars.append("ANTHROPIC_API_KEY")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        missing_vars.append("ELEVENLABS_API_KEY")

    # Check for optional but recommended API keys
    optional_missing = []
    if not os.environ.get("GOOGLE_API_KEY"):
        optional_missing.append("GOOGLE_API_KEY")
    if not os.environ.get("OPENAI_API_KEY"):
        optional_missing.append("OPENAI_API_KEY")

    return missing_vars, optional_missing


if __name__ == "__main__":
    # Check for required and optional API keys
    missing_vars, optional_missing = check_api_keys()

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

    if optional_missing:
        print("Warning: The following optional API keys are not set:")
        for var in optional_missing:
            print(f"  - {var}")
        print("Some functionality may be limited without these keys.")
        print("Press Enter to continue or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            sys.exit(0)

    # Run CLI
    cli()
