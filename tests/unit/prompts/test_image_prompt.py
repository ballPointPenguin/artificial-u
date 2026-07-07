"""Tests for the image prompt module."""

import pytest

from artificial_u.prompts.lecture_image import format_lecture_slide_prompt
from artificial_u.prompts.professor_image import format_professor_image_prompt


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
    assert "High resolution" in prompt
    assert "digital art" in prompt
    assert "semi-realistic" in prompt
    assert "Do not make this photorealistic" in prompt


@pytest.mark.unit
def test_professor_image_prompt_minimal():
    """Test professor image prompt generation with minimal data."""
    professor = MockProfessor(
        name="Dr. Sarah Chen",
    )

    prompt = format_professor_image_prompt(professor)

    # Check that the prompt contains basic elements
    assert "Dr. Sarah Chen" in prompt
    assert "High resolution" in prompt
    assert "digital art" in prompt
    assert "semi-realistic" in prompt


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


@pytest.mark.unit
def test_lecture_slide_prompt():
    """Test lecture slide image prompt generation and smart truncation."""
    professor = MockProfessor(
        name="Dr. Sarah Chen",
        title="Professor of Quantum Computing",
        gender="Female",
        age=45,
        description="Tall with short dark hair, often wears professional attire",
        specialization="Quantum Computing",
    )
    course = MockProfessor(
        code="CS101",
        title="Intro to Computing",
    )

    long_chunk_text = (
        "This is a very long chunk text that explains the fundamental principles of quantum superposition. "
        * 20
    )
    summary = "Lecture about quantum mechanics."

    prompt, refs = format_lecture_slide_prompt(
        professor=professor,
        course=course,
        lecture_summary=summary,
        chunk_text=long_chunk_text,
        previous_chunk_text="Previously, we discussed classical bits.",
        professor_image_url="https://example.com/prof.png",
        first_slide_url="https://example.com/first.png",
        previous_slide_url="https://example.com/prev.png",
        aspect_ratio="16:9",
    )

    # Check style and basic details are present
    assert "STYLE: Semi-realistic" in prompt
    assert "SUBJECT: Professor Dr. Sarah Chen" in prompt
    assert "Quantum Computing" in prompt
    assert "SETTING:" in prompt
    assert "ACTION/SCENE:" in prompt
    assert "COMPOSITION GUIDANCE:" in prompt
    assert "LIGHTING & ATMOSPHERE:" in prompt
    assert "ASPECT RATIO: 16:9" in prompt

    # Verify smart truncation works (the raw text was > 2000 chars, but should be truncated to ~600)
    assert "quantum superposition" in prompt
    assert len(prompt) < 3000  # Should be compact and focused

    # Verify reference URLs are returned correctly
    assert len(refs) == 3
    assert refs[0] == "https://example.com/prof.png"
    assert refs[1] == "https://example.com/first.png"
    assert refs[2] == "https://example.com/prev.png"
