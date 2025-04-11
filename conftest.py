"""
Global pytest configuration file.
Ensures tests use the proper environment settings.
"""

import os
import sys
import pytest

# Import the settings (this will auto-load .env.test in test environments)
from artificial_u.config.settings import get_settings


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


# Ensure environment is correctly set up for tests
if not is_manual_test():
    # For automated tests, make sure TESTING flag is set
    os.environ["TESTING"] = "true"
    print("Using TEST environment variables for automated tests")
else:
    # For manual tests, clear TESTING flag if set
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    print("Using REAL environment variables for manual tests")


@pytest.fixture(scope="session", autouse=True)
def verify_test_environment():
    """
    Verify test environment configuration:
    - For regular automated tests: Check we're using test values
    - For manual tests: Check we're using real values
    """
    # Get settings (will load the correct configuration based on environment)
    settings = get_settings()

    if not is_manual_test():
        # Verify we're using test credentials in automated tests
        assert settings.testing is True, "Settings should be in test mode"
        assert os.environ.get("TESTING") == "true", "TESTING flag should be set"
        assert (
            settings.environment.value == "testing"
        ), "Environment should be 'testing'"

        # Verify we have the expected test key values
        if settings.ELEVENLABS_API_KEY:
            assert (
                settings.ELEVENLABS_API_KEY == "test_elevenlabs_key"
            ), "Using incorrect ElevenLabs key"
        if settings.ANTHROPIC_API_KEY:
            assert (
                settings.ANTHROPIC_API_KEY == "test_anthropic_key"
            ), "Using incorrect Anthropic key"

    yield

    # No cleanup needed
