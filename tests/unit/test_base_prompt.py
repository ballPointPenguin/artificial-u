"""Tests for the prompt base utilities."""

import pytest

from artificial_u.prompts.base import (
    PromptTemplate,
    extract_xml_content,
)


@pytest.mark.unit
def test_prompt_template():
    """Test the PromptTemplate class."""
    template = PromptTemplate(template="Hello, {name}!", required_vars=["name"])

    # Test successful formatting
    result = template.format(name="World")
    assert result == "Hello, World!"

    # Test calling syntax
    result = template(name="Claude")
    assert result == "Hello, Claude!"

    # Test missing required variable
    with pytest.raises(ValueError):
        template.format()


@pytest.mark.unit
def test_extract_xml_content():
    """Test the extract_xml_content function."""
    text = "<test>content</test>"
    result = extract_xml_content(text, "test")
    assert result == "content"

    # Test with nested tags
    text = "<outer><inner>content</inner></outer>"
    result = extract_xml_content(text, "outer")
    assert result == "<inner>content</inner>"

    # Test with no match
    result = extract_xml_content(text, "nonexistent")
    assert result is None
