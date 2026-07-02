"""Tests for the course tags prompt module."""

import pytest

from artificial_u.prompts.fr.tags import get_course_tags_prompt as get_course_tags_prompt_fr
from artificial_u.prompts.tags import MAX_TOPIC_TITLES, get_course_tags_prompt

COURSE_DATA = {
    "code": "CS101",
    "title": "Introduction to Artificial Intelligence",
    "description": "Foundational concepts and techniques in AI.",
    "level": "Undergraduate",
    "lectures_per_week": 1,
    "total_weeks": 12,
}


@pytest.mark.unit
def test_tags_prompt_with_full_context():
    """Prompt includes course fields, department, topics, and vocabulary."""
    prompt = get_course_tags_prompt(
        COURSE_DATA,
        department_name="Computer Science",
        topic_titles=["Search Algorithms", "Neural Networks"],
        existing_tags=["Machine Learning", "Ethics"],
    )

    assert "CS101" in prompt
    assert "Introduction to Artificial Intelligence" in prompt
    assert "Computer Science" in prompt
    assert "Search Algorithms" in prompt
    assert "Machine Learning" in prompt
    assert "<tags>" in prompt
    assert "<tag>" in prompt
    assert "<output>" in prompt


@pytest.mark.unit
def test_tags_prompt_without_optional_context():
    """Prompt renders without department, topics, or vocabulary."""
    prompt = get_course_tags_prompt(COURSE_DATA)

    assert "CS101" in prompt
    assert "Department:" not in prompt
    assert "vocabulary" not in prompt.lower() or "Existing tag vocabulary" not in prompt


@pytest.mark.unit
def test_tags_prompt_caps_topic_titles():
    """Long syllabi are truncated to keep the prompt bounded."""
    titles = [f"Topic {i}" for i in range(MAX_TOPIC_TITLES + 20)]
    prompt = get_course_tags_prompt(COURSE_DATA, topic_titles=titles)

    assert prompt.count("- Topic ") == MAX_TOPIC_TITLES


@pytest.mark.unit
def test_tags_prompt_french_mirror():
    """The French module produces French instructions with the same slots."""
    prompt = get_course_tags_prompt_fr(
        COURSE_DATA,
        department_name="Informatique",
        topic_titles=["Algorithmes de recherche"],
        existing_tags=["Apprentissage Automatique"],
    )

    assert "CS101" in prompt
    assert "Informatique" in prompt
    assert "Apprentissage Automatique" in prompt
    assert "<tags>" in prompt
    assert "Générez des tags" in prompt
