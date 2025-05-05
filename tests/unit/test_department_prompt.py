"""Tests for the department prompt module."""

import pytest

from artificial_u.prompts.department import get_department_prompt


@pytest.mark.unit
def test_department_prompt_with_name():
    """Test department prompt generation with department name."""
    prompt = get_department_prompt(department_name="Computer Science")

    # Check that required elements are in the prompt
    assert "Computer Science" in prompt
    assert "<department>" in prompt
    assert "<name>" in prompt
    assert "<code>" in prompt
    assert "<faculty>" in prompt
    assert "<description>" in prompt


@pytest.mark.unit
def test_department_prompt_with_course():
    """Test department prompt generation with course name."""
    prompt = get_department_prompt(course_name="Introduction to Artificial Intelligence")

    # Check that required elements are in the prompt
    assert "Introduction to Artificial Intelligence" in prompt
    assert "<department>" in prompt
    assert "<name>" in prompt
    assert "<code>" in prompt
    assert "<faculty>" in prompt
    assert "<description>" in prompt


@pytest.mark.unit
def test_department_prompt_with_existing():
    """Test department prompt generation with existing departments."""
    existing_departments = [
        "Computer Science",
        "Mathematics",
        "Physics",
    ]

    prompt = get_department_prompt(existing_departments=existing_departments)

    # Check that existing departments are included
    assert "Computer Science" in prompt
    assert "Mathematics" in prompt
    assert "Physics" in prompt
    assert "<existing_departments>" in prompt
