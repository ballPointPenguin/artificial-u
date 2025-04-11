"""
Global pytest configuration file.
Ensures all tests use the test environment variables from .env.test
EXCEPT for manual tests which need real API credentials.
"""

import os
import sys
from dotenv import load_dotenv


# Check if we're running manual tests
def is_manual_test():
    """Check if we're running manual tests that need real credentials"""
    return any(arg in sys.argv for arg in ["-m manual", "manual"])


# Check if we're running unit tests
def is_unit_test():
    """Check if we're running unit tests"""
    return any(arg in sys.argv for arg in ["-m unit", "unit"])


# Custom collection logic to skip manual tests when running unit tests
def pytest_ignore_collect(path, config):
    """Skip collecting tests from manual directory when running unit tests"""
    if is_unit_test() and "tests/manual" in str(path):
        return True
    return False


# Load environment variables at the very beginning
if not is_manual_test():
    # Normal tests - load the test environment variables
    load_dotenv(".env.test", override=True)
    os.environ["TESTING"] = "true"
    print("Using TEST environment variables for automated tests")
else:
    # Manual tests - load regular .env file if available
    load_dotenv(".env")
    print("Using REAL environment variables for manual tests")

import pytest


@pytest.fixture(scope="session", autouse=True)
def load_env_vars():
    """
    Load environment variables appropriately for the test type:
    - For regular automated tests: Use .env.test with test credentials
    - For manual tests: Use real credentials from .env

    This is redundant with the load at the top, but kept to verify credentials.
    """
    if not is_manual_test():
        # Verify we're using test credentials
        assert os.environ.get("ELEVENLABS_API_KEY") == "test_elevenlabs_key"
        assert os.environ.get("ANTHROPIC_API_KEY") == "test_anthropic_key"

    yield

    # Clean up is not strictly necessary as environment variables persist only for the duration of the process
