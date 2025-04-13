"""
Ollama adapter for ArtificialU to use local models for testing.
"""

import os
import re
import signal
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import ollama


# Custom timeout exception
class OllamaTimeoutError(Exception):
    """Exception raised when Ollama request times out."""

    pass


# Timeout handler for Ollama requests
def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise OllamaTimeoutError("Ollama request timed out")


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

    def get_message_summary(self, messages, length=120):
        """Extract a short summary of the first message for debugging."""
        if not messages or not isinstance(messages, list) or not messages[0]:
            return "No messages"

        msg = messages[0]

        # Handle Anthropic's message format with content as a list
        if isinstance(msg.get("content"), list):
            for content_item in msg["content"]:
                if content_item.get("type") == "text" and content_item.get("text"):
                    text = content_item.get("text", "")
                    first_line = text.split("\n")[0]
                    return first_line[:length] + (
                        "..." if len(first_line) > length else ""
                    )

        # Handle simple string content
        elif isinstance(msg.get("content"), str):
            text = msg.get("content", "")
            first_line = text.split("\n")[0]
            return first_line[:length] + ("..." if len(first_line) > length else "")

        return "Unknown message format"

    def create(
        self,
        model: str = "tinyllama",
        max_tokens: int = 1000,
        temperature: float = 0.0,
        system: str = "",
        messages: List[Dict[str, str]] = None,
        timeout: int = 60,  # Default timeout of 60 seconds
    ) -> Any:
        """
        Create a completion using Ollama that mimics Anthropic's response format.
        For testing purposes, this will wrap Ollama's responses in expected XML tags.

        Args:
            model: The Ollama model to use, defaults to "tinyllama"
            max_tokens: Maximum number of tokens in the response
            temperature: Sampling temperature
            system: System prompt
            messages: List of message objects with role and content
            timeout: Maximum time in seconds to wait for a response

        Returns:
            A response object that mimics Anthropic's response structure
        """

        # Convert Anthropic-style messages to Ollama format
        ollama_messages = []

        # Add system message if provided
        if system:
            ollama_messages.append({"role": "system", "content": system})

        # Add user messages

        message_summary = self.get_message_summary(messages)
        ollama_messages.append({"role": "user", "content": message_summary})

        # Set up timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            # Call Ollama with timeout
            response = self.client.chat(
                model=model,
                messages=ollama_messages,
                options={
                    "temperature": 0.0,  # Zero temperature = more deterministic, faster
                    "num_predict": min(100, max_tokens),  # Generate much less text
                    # "num_ctx": 256,  # Smaller context window
                    # "num_thread": 2,  # Use fewer threads
                },
            )

            # Disable the alarm
            signal.alarm(0)
        except OllamaTimeoutError:
            # Return a simplified response if timeout occurs
            return OllamaContent(
                content=[
                    OllamaMessage(
                        text="Request timed out. Please try again with a simpler query or smaller model."
                    )
                ]
            )
        except Exception as e:
            # Disable the alarm for any other exception too
            signal.alarm(0)
            # Return a simplified error response
            return OllamaContent(
                content=[
                    OllamaMessage(text=f"Error communicating with Ollama: {str(e)}")
                ]
            )

        # Get the raw response text
        raw_text = response["message"]["content"]
        message = OllamaMessage(text=raw_text)
        result = OllamaContent(content=[message])
        return result
