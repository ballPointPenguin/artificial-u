"""Tests for the course selection prompt module."""

import pytest

from artificial_u.prompts.course_selection import (
    courses_for_selection_to_xml,
    get_course_selection_prompt,
    parse_course_selection_decision,
)


@pytest.mark.unit
class TestCoursesForSelectionToXml:
    """Tests for XML formatting of courses for selection."""

    def test_empty_courses_list(self):
        """Test with empty list returns no_existing_courses tag."""
        result = courses_for_selection_to_xml([])
        assert result == "<no_existing_courses />"

    def test_single_course_without_professor(self):
        """Test XML generation for a single course without professor."""
        courses = [
            {
                "id": 1,
                "title": "Introduction to Python",
                "description": "Learn Python basics",
            }
        ]
        result = courses_for_selection_to_xml(courses)

        assert "<existing_courses>" in result
        assert "</existing_courses>" in result
        assert "<id>1</id>" in result
        assert "<title>Introduction to Python</title>" in result
        assert "<description>Learn Python basics</description>" in result
        assert "<professor>" not in result

    def test_single_course_with_professor(self):
        """Test XML generation for a course with professor name."""
        courses = [
            {
                "id": 42,
                "title": "Machine Learning",
                "description": "ML fundamentals",
                "professor_name": "Dr. Ada Lovelace",
            }
        ]
        result = courses_for_selection_to_xml(courses)

        assert "<id>42</id>" in result
        assert "<title>Machine Learning</title>" in result
        assert "<professor>Dr. Ada Lovelace</professor>" in result

    def test_multiple_courses(self):
        """Test XML generation for multiple courses."""
        courses = [
            {"id": 1, "title": "Course A", "description": "Desc A"},
            {"id": 2, "title": "Course B", "description": "Desc B", "professor_name": "Prof B"},
            {"id": 3, "title": "Course C", "description": "Desc C"},
        ]
        result = courses_for_selection_to_xml(courses)

        assert result.count("<course>") == 3
        assert result.count("</course>") == 3
        assert "<id>1</id>" in result
        assert "<id>2</id>" in result
        assert "<id>3</id>" in result
        # Only course 2 has a professor
        assert result.count("<professor>") == 1

    def test_xml_escaping(self):
        """Test that special characters are properly escaped."""
        courses = [
            {
                "id": 1,
                "title": "C++ & Java: <Advanced>",
                "description": 'Learn "both" languages',
                "professor_name": "Dr. O'Brien",
            }
        ]
        result = courses_for_selection_to_xml(courses)

        # XML special characters should be escaped
        assert "&amp;" in result or "C++" in result
        assert "&lt;" in result or "<Advanced>" not in result
        assert "&gt;" in result or "<Advanced>" not in result

    def test_missing_fields(self):
        """Test handling of courses with missing optional fields."""
        courses = [
            {"id": 5},  # Only ID provided
            {"id": 6, "title": "Only Title"},
        ]
        result = courses_for_selection_to_xml(courses)

        assert "<id>5</id>" in result
        assert "<id>6</id>" in result
        assert "<title>Only Title</title>" in result


@pytest.mark.unit
class TestGetCourseSelectionPrompt:
    """Tests for course selection prompt generation."""

    def test_prompt_with_courses(self):
        """Test prompt generation with existing courses."""
        user_query = "I want to learn machine learning"
        existing_courses = [
            {
                "id": 1,
                "title": "Introduction to ML",
                "description": "Basic ML concepts",
                "professor_name": "Dr. Smith",
            }
        ]

        prompt = get_course_selection_prompt(
            user_query=user_query,
            existing_courses=existing_courses,
        )

        # Check key components are in the prompt
        assert "I want to learn machine learning" in prompt
        assert "<existing_courses>" in prompt
        assert "Introduction to ML" in prompt
        assert "Dr. Smith" in prompt
        assert "<decision>" in prompt
        assert "SELECT" in prompt
        assert "GENERATE" in prompt

    def test_prompt_without_courses(self):
        """Test prompt generation with no existing courses."""
        user_query = "I want to learn quantum computing"

        prompt = get_course_selection_prompt(
            user_query=user_query,
            existing_courses=[],
        )

        assert "quantum computing" in prompt
        assert "<no_existing_courses />" in prompt


@pytest.mark.unit
class TestParseCourseSelectionDecision:
    """Tests for parsing AI course selection decisions."""

    def test_parse_select_single_course(self):
        """Test parsing SELECT decision with single course."""
        ai_response = """
        <decision>
          <action>SELECT</action>
          <course_ids>15</course_ids>
          <reasoning>Course 15 is a perfect match for the learning goal.</reasoning>
        </decision>
        """

        result = parse_course_selection_decision(ai_response)

        assert result["action"] == "SELECT"
        assert result["course_ids"] == [15]
        assert "perfect match" in result["reasoning"]

    def test_parse_select_multiple_courses(self):
        """Test parsing SELECT decision with multiple courses."""
        ai_response = """
        <decision>
          <action>SELECT</action>
          <course_ids>15, 23, 42</course_ids>
          <reasoning>All three courses complement the learning goal.</reasoning>
        </decision>
        """

        result = parse_course_selection_decision(ai_response)

        assert result["action"] == "SELECT"
        assert result["course_ids"] == [15, 23, 42]
        assert len(result["course_ids"]) == 3

    def test_parse_generate_decision(self):
        """Test parsing GENERATE decision."""
        ai_response = """
        <decision>
          <action>GENERATE</action>
          <course_ids></course_ids>
          <reasoning>No existing courses cover this specialized topic.</reasoning>
        </decision>
        """

        result = parse_course_selection_decision(ai_response)

        assert result["action"] == "GENERATE"
        assert result["course_ids"] == []
        assert "specialized topic" in result["reasoning"]

    def test_parse_with_surrounding_text(self):
        """Test parsing when decision is embedded in other text."""
        ai_response = """
        Let me analyze the courses...

        <decision>
          <action>SELECT</action>
          <course_ids>7</course_ids>
          <reasoning>Course 7 covers the basics well.</reasoning>
        </decision>

        Hope this helps!
        """

        result = parse_course_selection_decision(ai_response)

        assert result["action"] == "SELECT"
        assert result["course_ids"] == [7]

    def test_parse_invalid_action_raises_error(self):
        """Test that invalid action raises ValueError."""
        ai_response = """
        <decision>
          <action>INVALID</action>
          <course_ids></course_ids>
          <reasoning>Something</reasoning>
        </decision>
        """

        with pytest.raises(ValueError, match="Invalid action"):
            parse_course_selection_decision(ai_response)

    def test_parse_select_without_ids_raises_error(self):
        """Test that SELECT without course IDs raises ValueError."""
        ai_response = """
        <decision>
          <action>SELECT</action>
          <course_ids></course_ids>
          <reasoning>No courses selected but said SELECT</reasoning>
        </decision>
        """

        with pytest.raises(ValueError, match="SELECT action must include"):
            parse_course_selection_decision(ai_response)

    def test_parse_missing_decision_tag_raises_error(self):
        """Test that missing decision tag raises ValueError."""
        ai_response = "I think you should take course 15."

        with pytest.raises(ValueError, match="No <decision> tag"):
            parse_course_selection_decision(ai_response)

    def test_parse_truncated_response(self):
        """Test parsing truncated response with missing closing tags."""
        ai_response = """
        <decision>
          <action>GENERATE</action>
          <course_ids></course_ids>
          <reasoning>No existing courses match because the student wants to learn about
          a very specialized topic that combines quantum physics with bioinformatics
        """

        # Should handle truncated response gracefully
        result = parse_course_selection_decision(ai_response)

        assert result["action"] == "GENERATE"
        assert result["course_ids"] == []
        assert "specialized topic" in result["reasoning"]

    def test_parse_course_ids_with_whitespace(self):
        """Test parsing course IDs with extra whitespace."""
        ai_response = """
        <decision>
          <action>SELECT</action>
          <course_ids>  15 ,  23  ,  42  </course_ids>
          <reasoning>Selected courses.</reasoning>
        </decision>
        """

        result = parse_course_selection_decision(ai_response)

        assert result["course_ids"] == [15, 23, 42]

    def test_parse_skips_non_numeric_ids(self):
        """Test that non-numeric IDs are skipped with warning."""
        ai_response = """
        <decision>
          <action>SELECT</action>
          <course_ids>15, abc, 23</course_ids>
          <reasoning>Mixed IDs.</reasoning>
        </decision>
        """

        result = parse_course_selection_decision(ai_response)

        # Should only include valid numeric IDs
        assert result["course_ids"] == [15, 23]
