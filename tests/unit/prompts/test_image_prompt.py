"""Tests for the image prompt module."""

import pytest

from artificial_u.prompts.images import format_professor_image_prompt


class MockProfessor:
    """Mock professor class for testing image prompts."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.unit
def test_professor_image_prompt_full():
    """Test professor image prompt generation with full data."""
    professor = MockProfessor(
        name="Dr. Sarah Chen",
        gender="Female",
        age=45,
        description="Tall with short dark hair, often wears professional attire",
        specialization="Quantum Computing",
    )

    prompt = format_professor_image_prompt(professor)

    # Check that required elements are in the prompt
    assert "Dr. Sarah Chen" in prompt
    assert "Female" in prompt
    assert "45" in prompt
    assert "Tall with short dark hair" in prompt
    assert "professional attire" in prompt
    assert "Quantum Computing" in prompt
    assert "high-resolution" in prompt
    assert "photorealistic" in prompt


@pytest.mark.unit
def test_professor_image_prompt_minimal():
    """Test professor image prompt generation with minimal data."""
    professor = MockProfessor(
        name="Dr. Sarah Chen",
    )

    prompt = format_professor_image_prompt(professor)

    # Check that the prompt contains basic elements
    assert "Dr. Sarah Chen" in prompt
    assert "high-resolution" in prompt
    assert "photorealistic" in prompt


@pytest.mark.unit
def test_professor_image_prompt_custom_ratio():
    """Test professor image prompt generation with custom aspect ratio."""
    professor = MockProfessor(
        name="Dr. Sarah Chen",
        gender="Female",
    )

    prompt = format_professor_image_prompt(professor, aspect_ratio="16:9")

    # Check that aspect ratio is included
    assert "Dr. Sarah Chen" in prompt
    assert "Female" in prompt
    assert "16:9" in prompt
