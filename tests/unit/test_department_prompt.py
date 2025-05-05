"""Tests for the department prompt module."""

import pytest

from artificial_u.prompts.department import get_department_prompt


@pytest.mark.unit
def test_department_prompt_with_partial_attributes():
    """Test department prompt generation with partial attributes."""
    partial_attrs = {
        "name": "Computer Science",
        "code": "CS",
    }

    prompt = get_department_prompt(partial_attributes=partial_attrs)

    # Check that required elements are in the prompt
    assert "Computer Science" in prompt
    assert "CS" in prompt
    assert "<department>" in prompt
    assert "<name>" in prompt
    assert "<code>" in prompt
    assert "<faculty>" in prompt
    assert "<description>" in prompt
    assert "XML Structure:" in prompt


@pytest.mark.unit
def test_department_prompt_with_freeform():
    """Test department prompt generation with freeform prompt."""
    freeform_text = "Create a department focused on artificial intelligence research"
    prompt = get_department_prompt(freeform_prompt=freeform_text)

    # Check that required elements are in the prompt
    assert freeform_text in prompt
    assert "<department>" in prompt
    assert "<name>" in prompt
    assert "<code>" in prompt
    assert "<faculty>" in prompt
    assert "<description>" in prompt
    assert "XML Structure:" in prompt


@pytest.mark.unit
def test_department_prompt_with_existing():
    """Test department prompt generation with existing departments."""
    existing_departments = [
        {"name": "Computer Science", "code": "CS"},
        {"name": "Mathematics", "code": "MTH"},
        {"name": "Physics", "code": "PHY"},
    ]

    prompt = get_department_prompt(existing_departments=existing_departments)

    # Check that existing departments are included
    assert "Computer Science" in prompt
    assert "Mathematics" in prompt
    assert "Physics" in prompt
    assert "CS" in prompt
    assert "MTH" in prompt
    assert "PHY" in prompt
    assert "<existing_departments>" in prompt


@pytest.mark.unit
def test_department_prompt_with_all_options():
    """Test department prompt generation with all available options."""
    existing_departments = [{"name": "Physics", "code": "PHY"}]
    partial_attrs = {"name": "Chemistry", "faculty": "Science and Technology"}
    freeform_text = "Focus on experimental chemistry research"

    prompt = get_department_prompt(
        existing_departments=existing_departments,
        partial_attributes=partial_attrs,
        freeform_prompt=freeform_text,
    )

    # Check that all elements are included
    assert "Physics" in prompt
    assert "PHY" in prompt
    assert "Chemistry" in prompt
    assert "Science and Technology" in prompt
    assert freeform_text in prompt
    assert "<existing_departments>" in prompt
    assert "<department>" in prompt


@pytest.mark.unit
def test_department_prompt_with_empty_inputs():
    """Test department prompt generation with empty inputs."""
    prompt = get_department_prompt()

    # Check that the basic structure is present
    assert "XML Structure:" in prompt
    assert "<department>" in prompt
    assert "<name>" in prompt
    assert "<code>" in prompt
    assert "<faculty>" in prompt
    assert "<description>" in prompt
    assert "Example 1:" in prompt
    assert "Example 2:" in prompt
