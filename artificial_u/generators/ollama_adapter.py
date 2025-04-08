"""
Ollama adapter for ArtificialU to use local models for testing.
"""

import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

import ollama


@dataclass
class OllamaMessage:
    """Class to mimic Anthropic message structure."""

    text: str


@dataclass
class OllamaContent:
    """Class to mimic Anthropic content structure."""

    content: List[OllamaMessage]


class OllamaClient:
    """
    Client adapter that mimics the Anthropic API client interface
    but uses Ollama under the hood for local model inference.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Ollama client adapter.

        Args:
            api_key: Not used but maintained for compatibility with Anthropic client
        """
        self.client = ollama
        self.messages = self

    def create(
        self,
        model: str = "tinyllama",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system: str = "",
        messages: List[Dict[str, str]] = None,
    ) -> Any:
        """
        Create a completion using Ollama that mimics Anthropic's response format.

        Args:
            model: The Ollama model to use, defaults to "tinyllama"
            max_tokens: Maximum number of tokens in the response
            temperature: Sampling temperature
            system: System prompt
            messages: List of message objects with role and content

        Returns:
            A response object that mimics Anthropic's response structure
        """
        # Convert Anthropic-style messages to Ollama format
        ollama_messages = []

        # Add system message if provided
        if system:
            ollama_messages.append({"role": "system", "content": system})

        # Add user messages
        if messages:
            for msg in messages:
                ollama_messages.append(msg)

        # Call Ollama
        response = self.client.chat(
            model=model,
            messages=ollama_messages,
            options={
                "temperature": temperature,
                # Note: Ollama doesn't have an exact max_tokens equivalent
                # but we're setting it for compatibility
                "num_predict": max_tokens,
            },
        )

        # Create an Anthropic-like response structure
        text = response["message"]["content"]
        message = OllamaMessage(text=text)

        result = OllamaContent(content=[message])
        return result
