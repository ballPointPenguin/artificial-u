"""
Test the generator factory functions.
"""

import os
import pytest
from unittest.mock import patch

from artificial_u.generators.factory import (
    create_default_generator,
    create_ollama_generator,
    create_generator,
)
from artificial_u.generators.content import ContentGenerator

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
def test_create_ollama_generator():
    """Test creating a generator with Ollama."""
    generator = create_ollama_generator()
    assert isinstance(generator, ContentGenerator)

    # Test with a specific model
    generator = create_ollama_generator(model="tinyllama")
    assert isinstance(generator, ContentGenerator)


@pytest.mark.integration
def test_create_generator_factory():
    """Test the main factory function."""
    with patch(
        "artificial_u.generators.factory.create_default_generator"
    ) as mock_default:
        create_generator(backend="anthropic", api_key="test_key")
        mock_default.assert_called_once_with(
            api_key="test_key", enable_caching=False, cache_metrics=True
        )

        mock_default.reset_mock()

        # Test with caching enabled
        create_generator(
            backend="anthropic",
            api_key="test_key",
            enable_caching=True,
            cache_metrics=False,
        )
        mock_default.assert_called_once_with(
            api_key="test_key", enable_caching=True, cache_metrics=False
        )

    with patch(
        "artificial_u.generators.factory.create_ollama_generator"
    ) as mock_ollama:
        create_generator(backend="ollama", model="tinyllama")
        mock_ollama.assert_called_once_with(model="tinyllama")

    # Test invalid backend
    with pytest.raises(ValueError):
        create_generator(backend="invalid")
