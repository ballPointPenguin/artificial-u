"""Test professor prompt generation."""

from artificial_u.prompts.professor import get_professor_prompt


def test_professor_prompt_with_partial_data():
    """Test professor prompt generation with partial data."""
    existing_professors = [
        {"name": "Dr. John Smith", "specialization": "Computer Science"},
        {"name": "Dr. Jane Doe", "specialization": "Mathematics"},
    ]

    partial_attributes = {
        "name": "Dr. Test Professor",
        "department_name": "Physics",
    }

    result = get_professor_prompt(existing_professors, partial_attributes)

    # Check that it contains the existing professors
    assert "Dr. John Smith" in result
    assert "Dr. Jane Doe" in result

    # Check that it contains the partial attributes
    assert "Dr. Test Professor" in result
    assert "Physics" in result


def test_professor_prompt_empty():
    """Test professor prompt generation with no data."""
    result = get_professor_prompt()

    # Should still contain the basic structure
    assert "professor" in result.lower()
    assert "generate" in result.lower()


def test_professor_prompt_with_only_existing():
    """Test professor prompt generation with only existing professors."""
    existing_professors = [
        {"name": "Dr. Existing", "specialization": "Chemistry"},
    ]

    result = get_professor_prompt(existing_professors)

    # Should contain existing professors
    assert "Dr. Existing" in result
    assert "Chemistry" in result


def test_professor_prompt_with_freeform_prompt():
    """Test professor prompt generation with freeform prompt."""
    existing_professors = [
        {"name": "Dr. John Smith", "specialization": "Computer Science"},
    ]

    partial_attributes = {
        "department_name": "Physics",
    }

    freeform_prompt = "Make this professor very eccentric and quirky"

    result = get_professor_prompt(
        existing_professors=existing_professors,
        partial_attributes=partial_attributes,
        freeform_prompt=freeform_prompt,
    )

    # Check that it contains the freeform prompt with improved framing
    assert "CONTEXT AND GUIDANCE:" in result
    assert "Make this professor very eccentric and quirky" in result

    # Check that it still contains other elements
    assert "Dr. John Smith" in result
    assert "Physics" in result


def test_professor_prompt_with_freeform_prompt_only():
    """Test professor prompt generation with only freeform prompt."""
    freeform_prompt = "Create a professor who specializes in ancient languages"

    result = get_professor_prompt(freeform_prompt=freeform_prompt)

    # Check that it contains the freeform prompt with improved framing
    assert "INSPIRATION AND CONTEXT:" in result
    assert "Create a professor who specializes in ancient languages" in result


def test_professor_prompt_without_freeform_prompt():
    """Test professor prompt generation without freeform prompt."""
    existing_professors = [
        {"name": "Dr. John Smith", "specialization": "Computer Science"},
    ]

    partial_attributes = {
        "department_name": "Physics",
    }

    result = get_professor_prompt(
        existing_professors=existing_professors, partial_attributes=partial_attributes
    )

    # Check that it does NOT contain freeform prompt text
    assert "IMPORTANT GUIDANCE:" not in result
    assert "INSPIRATION AND CONTEXT:" not in result
    assert "CONTEXT AND GUIDANCE:" not in result

    # Check that it still contains other elements
    assert "Dr. John Smith" in result
    assert "Physics" in result
