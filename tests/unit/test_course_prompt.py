"""Tests for the course prompt module."""

import pytest

from artificial_u.prompts.courses import get_course_prompt


@pytest.mark.unit
def test_course_prompt_with_full_data():
    """Test course prompt generation with complete data."""
    department_data = {
        "name": "Computer Science",
        "code": "CS",
        "faculty": "Science and Engineering",
        "description": "Study of computation and information",
    }

    professor_data = {
        "name": "Dr. Sarah Chen",
        "title": "Associate Professor",
        "specialization": "Machine Learning",
        "teaching_style": "Interactive and hands-on",
    }

    existing_courses = [
        {
            "code": "CS101",
            "title": "Introduction to Programming",
            "description": "Basic programming concepts",
            "topics": ["Variables", "Functions", "Loops"],
        },
    ]

    partial_course_attrs = {
        "code": "CS201",
        "title": "Data Structures",
        "level": "Undergraduate",
        "credits": 3,
    }

    prompt = get_course_prompt(
        department_data=department_data,
        professor_data=professor_data,
        existing_courses=existing_courses,
        partial_course_attrs=partial_course_attrs,
    )

    # Check that required elements are in the prompt
    assert "Computer Science" in prompt
    assert "Dr. Sarah Chen" in prompt
    assert "Machine Learning" in prompt
    assert "CS101" in prompt
    assert "Introduction to Programming" in prompt
    assert "CS201" in prompt
    assert "Data Structures" in prompt
    assert "<course>" in prompt
    assert "<existing_courses>" in prompt


@pytest.mark.unit
def test_course_prompt_with_freeform():
    """Test course prompt generation with freeform text."""
    department_data = {
        "name": "Computer Science",
        "code": "CS",
    }

    professor_data = {
        "name": "Dr. Sarah Chen",
        "specialization": "Machine Learning",
    }

    partial_course_attrs = {
        "code": "CS301",
        "title": "Machine Learning",
    }

    freeform_prompt = "Focus on practical applications and real-world examples."

    prompt = get_course_prompt(
        department_data=department_data,
        professor_data=professor_data,
        existing_courses=[],
        partial_course_attrs=partial_course_attrs,
        freeform_prompt=freeform_prompt,
    )

    # Check that freeform content is included
    assert "practical applications" in prompt
    assert "real-world examples" in prompt


@pytest.mark.unit
def test_course_prompt_minimal():
    """Test course prompt generation with minimal data."""
    department_data = {
        "name": "Computer Science",
    }

    professor_data = {
        "name": "Dr. Sarah Chen",
    }

    partial_course_attrs = {
        "code": "CS401",
    }

    prompt = get_course_prompt(
        department_data=department_data,
        professor_data=professor_data,
        existing_courses=[],
        partial_course_attrs=partial_course_attrs,
    )

    # Check that the prompt contains the basic structure and [GENERATE] markers
    assert "Computer Science" in prompt
    assert "Dr. Sarah Chen" in prompt
    assert "CS401" in prompt
    assert "[GENERATE]" in prompt
    assert "<course>" in prompt
    assert "<no_existing_courses />" in prompt
