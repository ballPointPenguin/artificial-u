"""Unit tests for course album-art image prompts."""

from artificial_u.models.core import Course, Professor
from artificial_u.prompts.course_image import format_course_image_prompt


def test_format_course_image_prompt_contains_core_sections():
    course = Course(
        id=1,
        code="CS101",
        title="Introduction to Testing",
        description="A course about unit tests and mocks.",
        level="Undergraduate",
        department_id=1,
        professor_id=1,
    )
    prompt = format_course_image_prompt(course, aspect_ratio="1:1")
    assert "Album art for a university course" in prompt
    assert "Introduction to Testing" in prompt
    assert "CS101" in prompt
    assert "Undergraduate" in prompt
    assert "unit tests" in prompt or "Themes" in prompt
    assert "0 and 12 words" in prompt
    assert "Negative Prompt" in prompt
    assert "Not photorealistic" in prompt
    assert "Aspect Ratio: 1:1" in prompt


def test_format_course_image_prompt_optional_professor():
    course = Course(
        id=2,
        code="ART99",
        title="Art History",
        description=None,
        level=None,
        department_id=1,
        professor_id=1,
    )
    prof = Professor(
        id=1,
        name="Dr. Example",
        title="Prof",
        specialization="Art",
        department_id=1,
    )
    prompt = format_course_image_prompt(course, professor=prof, aspect_ratio="16:9")
    assert "Dr. Example" in prompt
    assert "Aspect Ratio: 16:9" in prompt
