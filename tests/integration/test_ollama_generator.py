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


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
def test_content_generator_with_ollama():
    """Test that ContentGenerator works with the Ollama adapter."""
    # Create the OllamaClient with model preset
    ollama_client = OllamaClient()
    original_create = ollama_client.create

    # Configure model to use with Ollama without recursion
    def create_with_model(*args, **kwargs):
        kwargs["model"] = "tinyllama"
        return original_create(*args, **kwargs)

    # Override the create method to always use the specified model
    ollama_client.create = create_with_model

    # Create ContentGenerator with Ollama client
    generator = ContentGenerator(client=ollama_client)

    # Test creating a professor
    professor = generator.create_professor(
        department="Computer Science", specialization="Artificial Intelligence"
    )

    # The actual content doesn't matter, just that it runs without error
    assert isinstance(professor, Professor)
    assert professor.department == "Computer Science"


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
def test_create_lecture_with_ollama():
    """Test creating a lecture with Ollama."""
    # Create the OllamaClient
    ollama_client = OllamaClient()
    original_create = ollama_client.create

    # Configure model to use with Ollama without recursion
    def create_with_model(*args, **kwargs):
        kwargs["model"] = "tinyllama"
        return original_create(*args, **kwargs)

    # Override the create method to always use the specified model
    ollama_client.create = create_with_model

    # Create ContentGenerator with Ollama client
    generator = ContentGenerator(client=ollama_client)

    # Create a test professor and course
    professor = Professor(
        name="Dr. Test Professor",
        title="Professor of Testing",
        department="Computer Science",
        specialization="Software Testing",
        background="Extensive experience in testing",
        personality="Detail-oriented and methodical",
        teaching_style="Interactive with frequent code examples",
    )

    course = Course(
        id="TEST101",
        code="TEST101",
        title="Introduction to Software Testing",
        department="Computer Science",
        level="Undergraduate",
        credits=3,
        professor_id="test_prof",
        description="A comprehensive introduction to software testing principles",
        lectures_per_week=2,
        total_weeks=14,
    )

    # Generate a lecture
    lecture = generator.create_lecture(
        course=course,
        professor=professor,
        topic="Unit Testing Fundamentals",
        week_number=1,
        order_in_week=1,
        min_words=500,
        max_words=800,
    )

    # Validate the lecture
    assert isinstance(lecture, Lecture)
    assert lecture.course_id == course.id
    assert lecture.week_number == 1
    assert lecture.order_in_week == 1
    assert lecture.title == "Unit Testing Fundamentals"
    assert len(lecture.content) > 0  # Should have some content
