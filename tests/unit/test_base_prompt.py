"""Tests for the prompt base utilities."""

import pytest

from artificial_u.prompts.base import (
    PromptTemplate,
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
