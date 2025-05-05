"""Tests for the lecture prompt module."""

import pytest

from artificial_u.prompts.lectures import get_lecture_prompt


@pytest.mark.unit
def test_lecture_prompt_with_full_data():
    """Test lecture prompt generation with complete data."""
    professor_data = {
        "name": "Dr. Sarah Chen",
        "title": "Associate Professor",
        "specialization": "Quantum Computing",
        "personality": "Enthusiastic and engaging",
        "teaching_style": "Interactive with real-world examples",
    }

    existing_lectures = [
        {
            "title": "Introduction to Quantum States",
            "description": "Basic concepts of quantum states",
            "week_number": 1,
            "order_in_week": 1,
        },
    ]

    partial_lecture_attrs = {
        "title": "Quantum Superposition",
        "week_number": 1,
        "order_in_week": 2,
        "description": "Understanding quantum superposition",
    }

    prompt = get_lecture_prompt(
        professor_data=professor_data,
        existing_lectures=existing_lectures,
        partial_lecture_attrs=partial_lecture_attrs,
        word_count=2000,
    )

    # Check that required elements are in the prompt
    assert "Dr. Sarah Chen" in prompt
    assert "Quantum Computing" in prompt
    assert "Enthusiastic and engaging" in prompt
    assert "Interactive with real-world examples" in prompt
    assert "Introduction to Quantum States" in prompt
    assert "Quantum Superposition" in prompt
    assert "2000" in prompt
    assert "<lecture>" in prompt
    assert "<existing_lectures>" in prompt


@pytest.mark.unit
def test_lecture_prompt_with_freeform():
    """Test lecture prompt generation with freeform text."""
    professor_data = {
        "name": "Dr. Sarah Chen",
        "title": "Associate Professor",
        "teaching_style": "Interactive",
    }

    partial_lecture_attrs = {
        "title": "Quantum Superposition",
        "week_number": 1,
        "order_in_week": 1,
    }

    freeform_prompt = "Include a hands-on demonstration of superposition using a simple experiment."

    prompt = get_lecture_prompt(
        professor_data=professor_data,
        existing_lectures=[],
        partial_lecture_attrs=partial_lecture_attrs,
        freeform_prompt=freeform_prompt,
    )

    # Check that freeform content is included
    assert "hands-on demonstration" in prompt
    assert "simple experiment" in prompt


@pytest.mark.unit
def test_lecture_prompt_minimal():
    """Test lecture prompt generation with minimal data."""
    professor_data = {
        "name": "Dr. Sarah Chen",
    }

    partial_lecture_attrs = {
        "title": "Quantum Superposition",
    }

    prompt = get_lecture_prompt(
        professor_data=professor_data,
        existing_lectures=[],
        partial_lecture_attrs=partial_lecture_attrs,
    )

    # Check that the prompt contains the basic structure and [GENERATE] markers
    assert "Dr. Sarah Chen" in prompt
    assert "Quantum Superposition" in prompt
    assert "[GENERATE]" in prompt
    assert "<lecture>" in prompt
    assert "<no_existing_lectures />" in prompt
