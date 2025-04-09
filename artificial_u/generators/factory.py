"""
Factory functions for creating content generators with different backends.
"""

import os
from typing import Optional

from artificial_u.generators.content import ContentGenerator


def create_default_generator(
    api_key: Optional[str] = None,
    enable_caching: bool = False,
    cache_metrics: bool = True,
) -> ContentGenerator:
    """
    Create a default ContentGenerator using Anthropic.

    Args:
        api_key: Optional Anthropic API key, otherwise uses ANTHROPIC_API_KEY env var
        enable_caching: Whether to enable prompt caching
        cache_metrics: Whether to track cache metrics

    Returns:
        ContentGenerator: Generator instance using Anthropic
    """
    return ContentGenerator(
        api_key=api_key, enable_caching=enable_caching, cache_metrics=cache_metrics
    )


def create_ollama_generator(model: str = "tinyllama") -> ContentGenerator:
    """
    Create a ContentGenerator that uses Ollama for local inference.

    Args:
        model: Ollama model to use, defaults to 'tinyllama'

    Returns:
        ContentGenerator: Generator instance using Ollama

    Raises:
        ImportError: If ollama package is not installed
    """
    try:
        from artificial_u.generators.ollama_adapter import OllamaClient
    except ImportError:
        raise ImportError(
            "Ollama package not installed. Install with 'pip install ollama' "
            "or 'pip install -e .[dev]' to use this feature."
        )

    client = OllamaClient()

    # Store the original create method
    original_create = client.create

    # Configure model to use with Ollama
    def create_with_model(*args, **kwargs):
        kwargs["model"] = model
        return original_create(*args, **kwargs)

    # Override the create method to always use the specified model
    client.create = create_with_model

    # Create a wrapper for messages.create
    class MessagesWrapper:
        def create(self, *args, **kwargs):
            return create_with_model(*args, **kwargs)

    # Replace the messages attribute with our wrapper
    client.messages = MessagesWrapper()

    return ContentGenerator(client=client)


def create_generator(backend: str = "anthropic", **kwargs) -> ContentGenerator:
    """
    Factory function to create a ContentGenerator with the specified backend.

    Args:
        backend: Backend to use ('anthropic' or 'ollama')
        **kwargs: Backend-specific arguments
            - For 'anthropic': api_key, enable_caching, cache_metrics
            - For 'ollama': model

    Returns:
        ContentGenerator: Generator instance

    Raises:
        ValueError: If an invalid backend is specified
    """
    if backend == "anthropic":
        return create_default_generator(
            api_key=kwargs.get("api_key"),
            enable_caching=kwargs.get("enable_caching", False),
            cache_metrics=kwargs.get("cache_metrics", True),
        )
    elif backend == "ollama":
        return create_ollama_generator(model=kwargs.get("model", "tinyllama"))
    else:
        raise ValueError(f"Unknown backend: {backend}")
