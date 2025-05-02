"""
Global pytest configuration file.
Ensures tests use the proper environment settings.
"""

import os
import sys

import pytest

# Import the settings (this will auto-load .env.test in test environments)
from artificial_u.config.settings import get_settings

# Ensure environment is correctly set up for tests
# For automated tests, make sure TESTING flag is set
os.environ["TESTING"] = "true"
print("Using TEST environment variables for automated tests")


# Check if we're running unit tests
def is_unit_test():
    """Check if we're running unit tests"""
    return any(arg in sys.argv for arg in ["-m unit", "unit"])


@pytest.fixture(scope="session", autouse=True)
def verify_test_environment():
    """
    Verify test environment configuration:
    - For regular automated tests: Check we're using test values
    """
    # Get settings (will load the correct configuration based on environment)
    settings = get_settings()

    # Verify we're using test credentials in automated tests
    assert settings.testing is True, "Settings should be in test mode"
    assert os.environ.get("TESTING") == "true", "TESTING flag should be set"
    assert settings.environment.value == "testing", "Environment should be 'testing'"

    # Verify we have the expected test key values
    if settings.ELEVENLABS_API_KEY:
        assert (
            settings.ELEVENLABS_API_KEY == "test_elevenlabs_key"
        ), "Using incorrect ElevenLabs key"
    if settings.ANTHROPIC_API_KEY:
        assert (
            settings.ANTHROPIC_API_KEY == "test_anthropic_key"
        ), "Using incorrect Anthropic key"
    if settings.GOOGLE_API_KEY:
        assert (
            settings.GOOGLE_API_KEY == "test_google_key"
        ), "Using incorrect Google key"
    if settings.OPENAI_API_KEY:
        assert (
            settings.OPENAI_API_KEY == "test_openai_key"
        ), "Using incorrect OpenAI key"

    yield
