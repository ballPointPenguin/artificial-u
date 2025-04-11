"""
Test that the ContentGenerator works with Ollama for local development and testing.
"""

import os
import pytest
from unittest.mock import patch

from artificial_u.generators.content import ContentGenerator
from artificial_u.generators.ollama_adapter import OllamaClient
from artificial_u.models.core import Professor, Course, Lecture


# Skip these tests if Ollama is not installed or not running
ollama_installed = True
try:
    import ollama

    # Try to list models to check if Ollama server is running
    try:
        ollama.list()
        ollama_running = True
    except Exception:
        ollama_running = False
except ImportError:
    ollama_installed = False
    ollama_running = False

# Condition to skip tests
requires_ollama = pytest.mark.skipif(
    not (ollama_installed and ollama_running),
    reason="Ollama not installed or not running",
)

# Check if the tinyllama model is available
has_tinyllama = False
if ollama_running:
    models_data = ollama.list()
    model_names = [model.model for model in models_data.models]
    has_tinyllama = any("tinyllama" in model_name for model_name in model_names)
    print(f"Available models: {model_names}")
    print(f"Has TinyLlama: {has_tinyllama}")

# Skip if tinyllama is not available
requires_tinyllama = pytest.mark.skipif(
    not has_tinyllama,
    reason="TinyLlama model not available, run 'ollama pull tinyllama'",
)


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
def test_ollama_client_adapter():
    """Test that the OllamaClient adapter can be used as a drop-in replacement."""
    client = OllamaClient()

    # Test with a simple prompt
    response = client.create(
        model="tinyllama",
        max_tokens=100,
        temperature=0.7,
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Say hello!"}],
    )

    # Verify the response mimics the Anthropic structure
    assert hasattr(response, "content")
    assert len(response.content) > 0
    assert hasattr(response.content[0], "text")
    assert isinstance(response.content[0].text, str)
    assert len(response.content[0].text) > 0
