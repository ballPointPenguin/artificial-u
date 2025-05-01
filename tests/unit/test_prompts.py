"""Tests for the prompt module."""

import pytest

from artificial_u.prompts.base import (
    PromptTemplate,
    StructuredPrompt,
    extract_xml_content,
    xml_tag,
)
from artificial_u.prompts.lectures import StructuredLecturePrompt, get_lecture_prompt
from artificial_u.prompts.professors import get_professor_prompt
from artificial_u.prompts.system import get_system_prompt


class TestPromptBase:
    """Tests for the prompt base utilities."""

    @pytest.mark.unit
    def test_prompt_template(self):
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
    def test_structured_prompt(self):
        """Test the StructuredPrompt class."""
        prompt = StructuredPrompt()

        # Add sections
        prompt.add_section("greeting", "Hello, {name}!")
        prompt.add_section("farewell", "Goodbye, {name}!")

        # Test rendering
        expected = "Hello, {name}!\n\nGoodbye, {name}!"
        assert prompt.render() == expected

        # Test disabling a section
        prompt.disable_section("farewell")
        assert prompt.render() == "Hello, {name}!"

        # Test re-enabling a section
        prompt.enable_section("farewell")
        assert prompt.render() == expected

        # Test section ordering
        prompt = StructuredPrompt()
        prompt.add_section("b", "B")
        prompt.add_section("a", "A", position=0)
        prompt.add_section("c", "C")
        assert prompt.render() == "A\n\nB\n\nC"

    @pytest.mark.unit
    def test_xml_tag(self):
        """Test the xml_tag function."""
        result = xml_tag("test", "content")
        assert result == "<test>\ncontent\n</test>"

    @pytest.mark.unit
    def test_extract_xml_content(self):
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


class TestPromptModules:
    """Tests for the specific prompt modules."""

    @pytest.mark.unit
    def test_professor_prompt(self):
        """Test the professor prompt generator."""
        prompt = get_professor_prompt(
            department="Computer Science",
            specialization="Artificial Intelligence",
            gender="Male",
            nationality="Canadian",
            age_range="40-50",
        )

        # Check that required elements are in the prompt
        assert "Computer Science" in prompt
        assert "Artificial Intelligence" in prompt
        assert "Gender: Male" in prompt
        assert "Nationality/cultural background: Canadian" in prompt
        assert "Age range: 40-50" in prompt
        assert "<professor_profile>" in prompt

    @pytest.mark.unit
    def test_lecture_prompt(self):
        """Test the lecture prompt generator."""
        prompt = get_lecture_prompt(
            course_title="Introduction to Programming",
            course_code="CS101",
            topic="Variables and Data Types",
            week_number=1,
            order_in_week=1,
            professor_name="Dr. Smith",
            professor_background="PhD in Computer Science from MIT",
            teaching_style="Interactive and hands-on",
            professor_personality="Enthusiastic and patient",
            word_count=2000,
        )

        # Check that required elements are in the prompt
        assert "Introduction to Programming (CS101)" in prompt
        assert "Lecture Topic: Variables and Data Types" in prompt
        assert "Week: 1, Lecture: 1" in prompt
        assert "Name: Dr. Smith" in prompt
        assert "Background: PhD in Computer Science from MIT" in prompt
        assert "Teaching Style: Interactive and hands-on" in prompt
        assert "Personality: Enthusiastic and patient" in prompt
        assert "2000 words" in prompt
        assert "<lecture_preparation>" in prompt
        assert "<lecture_text>" in prompt

    @pytest.mark.unit
    def test_structured_lecture_prompt(self):
        """Test the StructuredLecturePrompt class."""
        prompt = StructuredLecturePrompt(word_count=1500)

        # Format the prompt
        formatted = prompt.format(
            course_title="AI Ethics",
            course_code="CS420",
            topic="Bias in Machine Learning",
            week_number=3,
            order_in_week=2,
            professor_name="Dr. Jones",
            professor_background="PhD in AI Ethics",
            teaching_style="Socratic method",
            professor_personality="Thoughtful and challenging",
        )

        # Check that required elements are in the formatted prompt
        assert "AI Ethics (CS420)" in formatted
        assert "Lecture Topic: Bias in Machine Learning" in formatted
        assert "Week: 3, Lecture: 2" in formatted
        assert "Name: Dr. Jones" in formatted
        assert "1500 words" in formatted

        # Test disabling a section
        prompt.disable_section("preparation_instructions")
        formatted = prompt.format(
            course_title="AI Ethics",
            course_code="CS420",
            topic="Bias in Machine Learning",
            week_number=3,
            order_in_week=2,
            professor_name="Dr. Jones",
            professor_background="PhD in AI Ethics",
            teaching_style="Socratic method",
            professor_personality="Thoughtful and challenging",
        )

        assert (
            "Consider how to structure the lecture for optimal audio delivery"
            not in formatted
        )

    @pytest.mark.unit
    def test_system_prompt(self):
        """Test the system prompt getter."""
        prompt = get_system_prompt("professor")
        assert "faculty profiles" in prompt

        prompt = get_system_prompt("course")
        assert "course topics" in prompt

        prompt = get_system_prompt("lecture")
        assert "educational content creator" in prompt

        # Test invalid prompt type
        with pytest.raises(ValueError):
            get_system_prompt("invalid")
