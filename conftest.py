"""
Global pytest configuration file.
Ensures all tests use the test environment variables from .env.test
EXCEPT for manual tests which need real API credentials.
"""

import os
import sys
import pytest
from dotenv import load_dotenv


def is_manual_test():
    """Check if we're running manual tests that need real credentials"""
    return any(arg in sys.argv for arg in ["-m manual", "manual"])


@pytest.fixture(scope="session", autouse=True)
def load_env_vars():
    """
    Load environment variables appropriately for the test type:
    - For regular automated tests: Use .env.test with test credentials
    - For manual tests: Use real credentials from .env
    """
    if not is_manual_test():
        # Normal tests - load the test environment variables
        load_dotenv(".env.test", override=True)

        # Set a flag to indicate we're running in test mode
        os.environ["TESTING"] = "true"

        # Verify we're using test credentials
        assert os.environ.get("ELEVENLABS_API_KEY") == "test_elevenlabs_key"
        assert os.environ.get("ANTHROPIC_API_KEY") == "test_anthropic_key"

        print("Using TEST environment variables for automated tests")
    else:
        # Manual tests - load regular .env file if available
        # These tests will skip themselves if real API keys aren't available
        load_dotenv(".env")
        print("Using REAL environment variables for manual tests")

    yield

    # Clean up is not strictly necessary as environment variables persist only for the duration of the process
