"""Tests for the lecture prompt module."""

import pytest

from artificial_u.prompts.lecture import get_lecture_prompt


@pytest.mark.unit
def test_lecture_prompt_with_full_data():
    """Test lecture prompt generation with complete data."""
    course_data = {
        "code": "CS101",
        "title": "Introduction to Computer Science",
        "credits": 3,
        "description": "Fundamentals of computer science",
        "lectures_per_week": 2,
        "level": "Undergraduate",
        "total_weeks": 14,
    }

    professor_data = {
        "name": "Dr. Sarah Chen",
        "title": "Associate Professor",
        "accent": "American",
        "age": 45,
        "background": "PhD in Computer Science from MIT",
        "description": "Expert in quantum computing",
        "gender": "Female",
        "personality": "Enthusiastic and engaging",
        "specialization": "Quantum Computing",
        "teaching_style": "Interactive with real-world examples",
    }

    topic_data = {
        "title": "Quantum Superposition",
        "week": 1,
        "order": 2,
    }

    existing_lectures = [
        {
            "week": 1,
            "order": 1,
            "title": "Introduction to Quantum States",
            "summary": "Basic concepts of quantum states",
        },
    ]

    topics_data = [
        {
            "title": "Introduction to Quantum States",
            "week": 1,
            "order": 1,
        },
        {
            "title": "Quantum Superposition",
            "week": 1,
            "order": 2,
        },
    ]

    prompt = get_lecture_prompt(
        course_data=course_data,
        professor_data=professor_data,
        topic_data=topic_data,
        existing_lectures=existing_lectures,
        topics_data=topics_data,
        word_count=2500,
    )

    # Check that required elements are in the prompt
    assert "CS101" in prompt
    assert "Introduction to Computer Science" in prompt
    assert "Dr. Sarah Chen" in prompt
    assert "Quantum Computing" in prompt
    assert "Enthusiastic and engaging" in prompt
    assert "Interactive with real-world examples" in prompt
    assert "Quantum Superposition" in prompt
    assert "2500" in prompt
    assert "<lecture>" in prompt
    assert "<existing_lectures>" in prompt
    assert "<topics>" in prompt


@pytest.mark.unit
def test_lecture_prompt_with_freeform():
    """Test lecture prompt generation with freeform text."""
    course_data = {
        "code": "CS101",
        "title": "Introduction to Computer Science",
    }

    professor_data = {
        "name": "Dr. Sarah Chen",
        "title": "Associate Professor",
        "teaching_style": "Interactive",
    }

    topic_data = {
        "title": "Quantum Superposition",
        "week": 1,
        "order": 1,
    }

    freeform_prompt = "Include a hands-on demonstration of superposition using a simple experiment."

    prompt = get_lecture_prompt(
        course_data=course_data,
        professor_data=professor_data,
        topic_data=topic_data,
        existing_lectures=[],
        topics_data=[],
        freeform_prompt=freeform_prompt,
    )

    # Check that freeform content is included
    assert "hands-on demonstration" in prompt
    assert "simple experiment" in prompt


@pytest.mark.unit
def test_lecture_prompt_minimal():
    """Test lecture prompt generation with minimal data."""
    course_data = {
        "code": "CS101",
        "title": "Introduction to Computer Science",
    }

    professor_data = {
        "name": "Dr. Sarah Chen",
    }

    topic_data = {
        "title": "Quantum Superposition",
        "week": 1,
        "order": 1,
    }

    prompt = get_lecture_prompt(
        course_data=course_data,
        professor_data=professor_data,
        topic_data=topic_data,
        existing_lectures=[],
        topics_data=[],
    )

    # Check that the prompt contains the basic structure and [GENERATE] markers
    assert "CS101" in prompt
    assert "Dr. Sarah Chen" in prompt
    assert "Quantum Superposition" in prompt
    assert "[GENERATE]" in prompt
    assert "<lecture>" in prompt
    assert "<no_existing_lectures />" in prompt
    assert "<no_existing_topics />" in prompt
