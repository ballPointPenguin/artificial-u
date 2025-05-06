"""Tests for the professor prompt module."""

import pytest

from artificial_u.prompts.professor import get_professor_prompt


@pytest.mark.unit
def test_professor_prompt_with_partial_data():
    """Test professor prompt generation with partial data."""
    partial_attributes = {
        "department_name": "Computer Science",
        "specialization": "Artificial Intelligence",
        "gender": "Male",
        "accent": "Canadian",
        "age": "50",
    }

    existing_professors = [
        {
            "name": "Dr. Smith",
            "specialization": "Cultural Anthropology",
        }
    ]

    prompt = get_professor_prompt(
        existing_professors=existing_professors,
        partial_attributes=partial_attributes,
    )

    # Check that required elements are in the prompt
    assert "Computer Science" in prompt
    assert "Artificial Intelligence" in prompt
    assert "Male" in prompt
    assert "Canadian" in prompt
    assert "50" in prompt
    assert "<professor>" in prompt
    assert "<existing_professors>" in prompt
    assert "Dr. Smith" in prompt
    assert "Cultural Anthropology" in prompt


@pytest.mark.unit
def test_professor_prompt_empty():
    """Test professor prompt generation with no data."""
    prompt = get_professor_prompt()

    # Check that the prompt contains the basic structure
    assert "<no_existing_professors />" in prompt
    assert "<professor>" in prompt
    assert "[GENERATE]" in prompt


@pytest.mark.unit
def test_professor_prompt_with_only_existing():
    """Test professor prompt generation with only existing professors."""
    existing_professors = [
        {
            "name": "Dr. Smith",
            "specialization": "Cultural Anthropology",
        },
        {
            "name": "Dr. Jones",
            "specialization": "Quantum Physics",
        },
    ]

    prompt = get_professor_prompt(existing_professors=existing_professors)

    # Check that existing professors are included
    assert "Dr. Smith" in prompt
    assert "Cultural Anthropology" in prompt
    assert "Dr. Jones" in prompt
    assert "Quantum Physics" in prompt
    assert "<existing_professors>" in prompt
