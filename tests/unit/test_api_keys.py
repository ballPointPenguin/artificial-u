"""
Test that API keys are properly loaded in test environment.
"""

import os

import pytest


@pytest.mark.unit
def test_environment_variables_are_set():
    """Test that required API keys have test values in the test environment."""
    # Verify ElevenLabs API key
    assert (
        os.environ.get("ELEVENLABS_API_KEY") == "test_elevenlabs_key"
    ), "ElevenLabs API key not set to test value"

    # Verify Anthropic API key
    assert (
        os.environ.get("ANTHROPIC_API_KEY") == "test_anthropic_key"
    ), "Anthropic API key not set to test value"

    # Verify OpenAI API key
    assert (
        os.environ.get("OPENAI_API_KEY") == "test_openai_key"
    ), "OpenAI API key not set to test value"

    # Verify we're in a test environment
    assert (
        os.environ.get("TESTING") == "true"
    ), "TESTING environment variable should be 'true'"
