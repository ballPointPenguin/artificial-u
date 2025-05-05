"""Tests for the system prompt module."""

import pytest

from artificial_u.prompts.system import get_system_prompt


@pytest.mark.unit
def test_system_prompt_professor():
    """Test getting professor system prompt."""
    prompt = get_system_prompt("professor")
    assert "faculty profiles" in prompt
    assert "XML format" in prompt


@pytest.mark.unit
def test_system_prompt_course():
    """Test getting course system prompt."""
    prompt = get_system_prompt("course")
    assert "course topics" in prompt
    assert "XML format" in prompt


@pytest.mark.unit
def test_system_prompt_department():
    """Test getting department system prompt."""
    prompt = get_system_prompt("department")
    assert "department profiles" in prompt
    assert "XML format" in prompt


@pytest.mark.unit
def test_system_prompt_lecture():
    """Test getting lecture system prompt."""
    prompt = get_system_prompt("lecture")
    assert "educational content creator" in prompt
    assert "XML format" in prompt


@pytest.mark.unit
def test_system_prompt_invalid():
    """Test getting system prompt with invalid type."""
    with pytest.raises(ValueError):
        get_system_prompt("invalid")


@pytest.mark.unit
def test_system_prompt_generic():
    """Test getting generic XML system prompt."""
    prompt = get_system_prompt("generic")
    assert "XML format" in prompt
    assert "any explanations" in prompt
