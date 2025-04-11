"""
Ollama adapter for ArtificialU to use local models for testing.
"""

import os
import signal
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import re

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

    def create(
        self,
        model: str = "tinyllama",
        max_tokens: int = 1000,
        temperature: float = 0.7,
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
        if messages:
            for msg in messages:
                # Handle Anthropic's new message format where content is a list of objects
                if isinstance(msg.get("content"), list):
                    # Extract text content from the list of content objects
                    text_content = ""
                    for content_item in msg["content"]:
                        if content_item.get("type") == "text":
                            text_content += content_item.get("text", "")
                    ollama_messages.append(
                        {"role": msg["role"], "content": text_content}
                    )
                else:
                    # Handle old format or simple string content
                    ollama_messages.append(msg)

        # Set up timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            # Call Ollama with timeout
            response = self.client.chat(
                model=model,
                messages=ollama_messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
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

        # Detect which type of content we're dealing with based on the prompt
        has_professor_profile = any(
            "<professor_profile>" in str(msg.get("content", ""))
            for msg in ollama_messages
        )
        has_syllabus = any(
            "<syllabus>" in str(msg.get("content", "")) for msg in ollama_messages
        )
        has_lecture = any(
            "<lecture>" in str(msg.get("content", "")) for msg in ollama_messages
        )

        if has_professor_profile:
            text = f"""<professor_profile>
Name: Dr. Test Professor
Title: Assistant Professor
Background: PhD in relevant field with research experience
Personality: Engaging and enthusiastic
Teaching Style: Interactive and student-focused
</professor_profile>"""
        elif has_syllabus:
            text = f"""<syllabus>
Course Description: A comprehensive introduction to the subject.

Learning Outcomes:
1. Understand key concepts
2. Apply theoretical knowledge
3. Develop critical thinking skills

Course Structure:
Weekly lectures and assignments

Assessment Methods:
- Midterm exam (30%)
- Final exam (40%)
- Assignments (30%)

Required Materials:
- Main textbook
- Course materials

Course Policies:
Standard academic policies apply
</syllabus>"""
        elif has_lecture:
            # Extract topic from the prompt using regex
            topic_pattern = r"Lecture Topic: (.*?)(?:\n|$)"
            topic_matches = (
                re.search(topic_pattern, str(msg.get("content", "")), re.IGNORECASE)
                for msg in ollama_messages
            )
            topic_match = next((match for match in topic_matches if match), None)
            topic = topic_match.group(1).strip() if topic_match else "Untitled Lecture"

            # Extract the actual generated content, skipping the prompt text
            content_pattern = r"\[.*?\].*?\[.*?\](.*)"
            content_match = re.search(content_pattern, raw_text, re.DOTALL)
            lecture_content = (
                content_match.group(1).strip() if content_match else raw_text
            )

            text = f"""<lecture_preparation>
Main Points:
1. Introduction to {topic}
2. Key concepts and principles
3. Examples and applications
4. Practice exercises
5. Summary and review
</lecture_preparation>

<lecture>
{topic}

{lecture_content}
</lecture>"""
        else:
            # Default case - just use the raw text
            text = raw_text

        message = OllamaMessage(text=text)
        result = OllamaContent(content=[message])
        return result
