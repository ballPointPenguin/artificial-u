"""
Unit tests for the converters module.
"""

import xml.etree.ElementTree as ET

import pytest

from artificial_u.models.converters import (
    course_model_to_dict,
    courses_to_xml,
    department_model_to_dict,
    department_to_xml,
    departments_to_xml,
    extract_xml_content,
    lecture_to_xml,
    lectures_to_xml,
    parse_course_xml,
    parse_lecture_xml,
    partial_course_to_xml,
    partial_lecture_to_xml,
    partial_professor_to_xml,
    professor_model_to_dict,
    professor_to_xml,
    professors_to_xml,
)


class MockModel:
    """Mock model class for testing converters."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.unit
def test_professor_model_to_dict():
    """Test converting a professor model to a dictionary."""
    # Test with None
    assert professor_model_to_dict(None) == {}

    # Test with a populated model
    professor = MockModel(
        id=1,
        name="Dr. Jane Smith",
        title="Associate Professor",
        department_id=2,
        specialization="Machine Learning",
        background="PhD from Stanford",
        personality="Engaging",
        teaching_style="Interactive",
        gender="Female",
        accent="American",
        description="Expert in ML",
        age=35,
        voice_id=3,
        image_url="https://example.com/jane.jpg",
    )

    result = professor_model_to_dict(professor)

    assert result["id"] == 1
    assert result["name"] == "Dr. Jane Smith"
    assert result["title"] == "Associate Professor"
    assert result["department_id"] == 2
    assert result["specialization"] == "Machine Learning"
    assert result["background"] == "PhD from Stanford"
    assert result["personality"] == "Engaging"
    assert result["teaching_style"] == "Interactive"
    assert result["gender"] == "Female"
    assert result["accent"] == "American"
    assert result["description"] == "Expert in ML"
    assert result["age"] == 35
    assert result["voice_id"] == 3
    assert result["image_url"] == "https://example.com/jane.jpg"


@pytest.mark.unit
def test_department_model_to_dict():
    """Test converting a department model to a dictionary."""
    # Test with None
    assert department_model_to_dict(None) == {}

    # Test with a populated model
    department = MockModel(
        id=1,
        name="Computer Science",
        code="CS",
        faculty="Science and Engineering",
        description="Study of computation",
    )

    result = department_model_to_dict(department)

    assert result["id"] == 1
    assert result["name"] == "Computer Science"
    assert result["code"] == "CS"
    assert result["faculty"] == "Science and Engineering"
    assert result["description"] == "Study of computation"


@pytest.mark.unit
def test_course_model_to_dict():
    """Test converting a course model to a dictionary."""
    # Test with None
    assert course_model_to_dict(None) == {}

    # Test with a populated model
    course = MockModel(
        id=1,
        code="CS101",
        title="Introduction to Programming",
        department_id=2,
        level="Undergraduate",
        credits=3,
        professor_id=3,
        description="Basic programming concepts",
        lectures_per_week=2,
        total_weeks=14,
        topics=["Variables", "Functions", "Loops"],
    )

    result = course_model_to_dict(course)

    assert result["id"] == 1
    assert result["code"] == "CS101"
    assert result["title"] == "Introduction to Programming"
    assert result["department_id"] == 2
    assert result["level"] == "Undergraduate"
    assert result["credits"] == 3
    assert result["professor_id"] == 3
    assert result["description"] == "Basic programming concepts"
    assert result["lectures_per_week"] == 2
    assert result["total_weeks"] == 14
    assert result["topics"] == ["Variables", "Functions", "Loops"]


@pytest.mark.unit
def test_professor_to_xml():
    """Test converting professor data to XML format."""
    # Test with empty data
    assert professor_to_xml({}) == "<professor>[GENERATE]</professor>"

    # Test with populated data
    professor_data = {
        "name": "Dr. Jane Smith",
        "title": "Associate Professor",
        "specialization": "Machine Learning",
        "personality": "Engaging",
        "teaching_style": "Interactive",
    }

    xml_str = professor_to_xml(professor_data)

    # Parse the XML to validate structure
    root = ET.fromstring(xml_str)
    assert root.tag == "professor"
    assert root.find("name").text == "Dr. Jane Smith"
    assert root.find("title").text == "Associate Professor"
    assert root.find("specialization").text == "Machine Learning"
    assert root.find("personality").text == "Engaging"
    assert root.find("teaching_style").text == "Interactive"

    # Test with partial data and custom missing marker
    partial_data = {
        "name": "Dr. Jane Smith",
        "title": "Associate Professor",
    }

    xml_str = professor_to_xml(partial_data, missing_marker="[TODO]")
    root = ET.fromstring(xml_str)
    assert root.find("name").text == "Dr. Jane Smith"
    assert root.find("title").text == "Associate Professor"
    assert root.find("specialization").text == "[TODO]"
    assert root.find("personality").text == "[TODO]"
    assert root.find("teaching_style").text == "[TODO]"


@pytest.mark.unit
def test_partial_professor_to_xml():
    """Test converting partial professor attributes to XML."""
    # Test with empty data
    empty_xml = partial_professor_to_xml({})
    root = ET.fromstring(empty_xml)
    assert root.tag == "professor"
    assert len(root) == 11  # Should have all 11 fields with [GENERATE]

    # Test with partial data
    partial_data = {
        "name": "Dr. Jane Smith",
        "title": "Associate Professor",
        "department_name": "Computer Science",
        "specialization": "Machine Learning",
    }

    xml_str = partial_professor_to_xml(partial_data)
    root = ET.fromstring(xml_str)
    assert root.find("name").text == "Dr. Jane Smith"
    assert root.find("title").text == "Associate Professor"
    assert root.find("department_name").text == "Computer Science"
    assert root.find("specialization").text == "Machine Learning"
    assert root.find("gender").text == "[GENERATE]"
    assert root.find("age").text == "[GENERATE]"


@pytest.mark.unit
def test_professors_to_xml():
    """Test converting a list of professors to XML."""
    # Test with empty list
    assert professors_to_xml([]) == "<no_existing_professors />"

    # Test with populated list
    professors = [
        {"name": "Dr. Jane Smith", "specialization": "Machine Learning"},
        {"name": "Dr. John Doe", "specialization": "Databases"},
    ]

    xml_str = professors_to_xml(professors)
    root = ET.fromstring(xml_str)
    assert root.tag == "existing_professors"
    assert len(root) == 2

    profs = root.findall("professor")
    assert profs[0].find("name").text == "Dr. Jane Smith"
    assert profs[0].find("specialization").text == "Machine Learning"
    assert profs[1].find("name").text == "Dr. John Doe"
    assert profs[1].find("specialization").text == "Databases"


@pytest.mark.unit
def test_department_to_xml():
    """Test converting department data to XML."""
    # Test with empty data
    assert department_to_xml({}) == "<department>[GENERATE]</department>"

    # Test with populated data
    department_data = {
        "name": "Computer Science",
        "code": "CS",
        "faculty": "Science and Engineering",
        "description": "Study of computation",
    }

    xml_str = department_to_xml(department_data)
    root = ET.fromstring(xml_str)
    assert root.tag == "department"
    assert root.find("name").text == "Computer Science"
    assert root.find("code").text == "CS"
    assert root.find("faculty").text == "Science and Engineering"
    assert root.find("description").text == "Study of computation"


@pytest.mark.unit
def test_departments_to_xml():
    """Test converting a list of department names to XML."""
    # Test with empty list
    assert departments_to_xml([]) == ""

    # Test with populated list
    departments = ["Computer Science", "Mathematics", "Physics"]

    xml_str = departments_to_xml(departments)
    lines = xml_str.strip().split("\n")
    assert len(lines) == 3
    assert lines[0] == "<department>Computer Science</department>"
    assert lines[1] == "<department>Mathematics</department>"
    assert lines[2] == "<department>Physics</department>"


@pytest.mark.unit
def test_courses_to_xml():
    """Test converting a list of courses to XML."""
    # Test with empty list
    assert courses_to_xml([]) == "<no_existing_courses />"

    # Test with populated list
    courses = [
        {
            "code": "CS101",
            "title": "Introduction to Programming",
            "description": "Basic programming concepts",
            "topics": ["Variables", "Functions", "Loops", "Conditionals", "Objects", "Classes"],
        },
        {
            "code": "CS201",
            "title": "Data Structures",
            "description": "Advanced data structures",
            "topics": ["Arrays", "Linked Lists", "Trees"],
        },
    ]

    # Test with topics included
    xml_str = courses_to_xml(courses, include_topics=True, max_topics=3)
    root = ET.fromstring(xml_str)
    assert root.tag == "existing_courses"
    assert len(root) == 2

    course_elems = root.findall("course")

    # Check first course
    assert course_elems[0].find("code").text == "CS101"
    topics_overview = course_elems[0].find("topics_overview")
    assert len(topics_overview.findall("topic")) == 3  # Limited to max_topics=3
    assert topics_overview.find("additional_topics_count").text.strip() == "3"  # 6-3=3 more topics

    # Check second course
    assert course_elems[1].find("code").text == "CS201"
    topics_overview = course_elems[1].find("topics_overview")
    assert len(topics_overview.findall("topic")) == 3
    assert topics_overview.find("additional_topics_count") is None  # No additional topics

    # Test without topics
    xml_str = courses_to_xml(courses, include_topics=False)
    root = ET.fromstring(xml_str)
    course_elems = root.findall("course")
    assert course_elems[0].find("topics_overview") is None


@pytest.mark.unit
def test_partial_course_to_xml():
    """Test converting partial course attributes to XML."""
    # Test with empty data
    empty_xml = partial_course_to_xml({})
    root = ET.fromstring(empty_xml)
    assert root.tag == "course"
    assert len(root.findall("*")) == 8  # 7 fields + topics

    # Test with partial data
    partial_data = {
        "code": "CS101",
        "title": "Introduction to Programming",
        "description": "Basic programming concepts",
        "level": "Undergraduate",
        "topics": [
            {"week": 1, "lecture": 1, "topic": "Introduction to Variables"},
            {"week": 1, "lecture": 2, "topic": "Control Flow"},
        ],
    }

    xml_str = partial_course_to_xml(partial_data)
    root = ET.fromstring(xml_str)
    assert root.find("code").text == "CS101"
    assert root.find("title").text == "Introduction to Programming"
    assert root.find("description").text == "Basic programming concepts"
    assert root.find("level").text == "Undergraduate"
    assert root.find("credits").text == "[GENERATE]"

    topics_elem = root.find("topics")
    weeks = topics_elem.findall("week")
    assert len(weeks) == 2
    assert weeks[0].get("number") == "1"
    lecture = weeks[0].find("lecture")
    assert lecture.get("number") == "1"
    assert lecture.find("topic").text == "Introduction to Variables"


@pytest.mark.unit
def test_parse_course_xml():
    """Test parsing course XML into a dictionary."""
    # Create a valid course XML
    course_xml = """
    <course>
      <code>CS101</code>
      <title>Introduction to Programming</title>
      <description>Basic programming concepts</description>
      <level>Undergraduate</level>
      <credits>3</credits>
      <lectures_per_week>2</lectures_per_week>
      <total_weeks>14</total_weeks>
      <topics>
        <week number="1">
          <lecture number="1">
            <topic>Introduction to Variables</topic>
          </lecture>
          <lecture number="2">
            <topic>Control Flow</topic>
          </lecture>
        </week>
        <week number="2">
          <lecture number="1">
            <topic>Functions</topic>
          </lecture>
        </week>
      </topics>
    </course>
    """

    result = parse_course_xml(course_xml)

    assert result["code"] == "CS101"
    assert result["title"] == "Introduction to Programming"
    assert result["description"] == "Basic programming concepts"
    assert result["level"] == "Undergraduate"
    assert result["credits"] == 3
    assert result["lectures_per_week"] == 2
    assert result["total_weeks"] == 14

    # Check topics
    topics = result["topics"]
    assert len(topics) == 3
    assert topics[0]["week_number"] == 1
    assert topics[0]["order_in_week"] == 1
    assert topics[0]["title"] == "Introduction to Variables"
    assert topics[1]["week_number"] == 1
    assert topics[1]["order_in_week"] == 2
    assert topics[1]["title"] == "Control Flow"
    assert topics[2]["week_number"] == 2
    assert topics[2]["order_in_week"] == 1
    assert topics[2]["title"] == "Functions"

    # Test handling of generate placeholders
    placeholder_xml = """
    <course>
      <code>CS101</code>
      <title>[GENERATE]</title>
      <description>Basic programming concepts</description>
      <level>Undergraduate</level>
      <credits>[GENERATE]</credits>
    </course>
    """

    result = parse_course_xml(placeholder_xml)
    assert result["code"] == "CS101"
    assert result["title"] is None  # [GENERATE] values should be None
    assert result["description"] == "Basic programming concepts"
    assert result["level"] == "Undergraduate"
    assert result["credits"] is None

    # Test error handling
    with pytest.raises(ValueError):
        parse_course_xml("<invalid>XML</with>")


@pytest.mark.unit
def test_lecture_to_xml():
    """Test converting lecture data to XML format."""
    # Test with empty data
    assert lecture_to_xml({}) == "<lecture>[GENERATE]</lecture>"

    # Test with populated data
    lecture_data = {
        "title": "Introduction to Variables",
        "content": "Today we'll learn about variables...",
        "description": "Understanding basic variable concepts",
    }

    xml_str = lecture_to_xml(lecture_data)

    # Parse the XML to validate structure
    root = ET.fromstring(xml_str)
    assert root.tag == "lecture"
    assert root.find("title").text == "Introduction to Variables"
    assert root.find("content").text == "Today we'll learn about variables..."
    assert root.find("description").text == "Understanding basic variable concepts"

    # Test with partial data and custom missing marker
    partial_data = {
        "title": "Introduction to Variables",
        "description": "Understanding basic variable concepts",
    }

    xml_str = lecture_to_xml(partial_data, missing_marker="[TODO]")
    root = ET.fromstring(xml_str)
    assert root.find("title").text == "Introduction to Variables"
    assert root.find("description").text == "Understanding basic variable concepts"
    assert root.find("content").text == "[TODO]"


@pytest.mark.unit
def test_lectures_to_xml():
    """Test converting a list of lectures to XML."""
    # Test with empty list
    assert lectures_to_xml([]) == "<no_existing_lectures />"

    # Test with populated list
    lectures = [
        {
            "title": "Introduction to Variables",
            "description": "Basic variable concepts",
            "week_number": 1,
            "order_in_week": 1,
        },
        {
            "title": "Control Flow",
            "description": "Understanding loops and conditionals",
            "week_number": 1,
            "order_in_week": 2,
        },
        {
            "title": "Functions",
            "description": "Working with functions",
            "week_number": 2,
            "order_in_week": 1,
        },
    ]

    # Test with default max_lectures
    xml_str = lectures_to_xml(lectures)
    root = ET.fromstring(xml_str)
    assert root.tag == "existing_lectures"
    assert len(root.findall("lecture")) == 3

    lecture_elems = root.findall("lecture")
    assert lecture_elems[0].find("title").text == "Introduction to Variables"
    assert lecture_elems[0].find("week_number").text == "1"
    assert lecture_elems[0].find("order_in_week").text == "1"

    # Test with max_lectures limit
    xml_str = lectures_to_xml(lectures, max_lectures=2)
    root = ET.fromstring(xml_str)
    assert len(root.findall("lecture")) == 2
    assert root.find("additional_lectures_count").text.strip() == "1"


@pytest.mark.unit
def test_partial_lecture_to_xml():
    """Test converting partial lecture attributes to XML."""
    # Test with empty data
    empty_xml = partial_lecture_to_xml({})
    root = ET.fromstring(empty_xml)
    assert root.tag == "lecture"
    assert len(root.findall("*")) == 5  # All fields should be present with [GENERATE]

    # Test with partial data
    partial_data = {
        "title": "Introduction to Variables",
        "week_number": 1,
        "order_in_week": 1,
        "description": "Understanding variables",
    }

    xml_str = partial_lecture_to_xml(partial_data)
    root = ET.fromstring(xml_str)
    assert root.find("title").text == "Introduction to Variables"
    assert root.find("week_number").text == "1"
    assert root.find("order_in_week").text == "1"
    assert root.find("description").text == "Understanding variables"
    assert root.find("content").text == "[GENERATE]"

    # Test with custom generate marker
    xml_str = partial_lecture_to_xml(partial_data, generate_marker="[TODO]")
    root = ET.fromstring(xml_str)
    assert root.find("content").text == "[TODO]"


@pytest.mark.unit
def test_parse_lecture_xml():
    """Test parsing lecture XML into a dictionary."""
    # Create a valid lecture XML
    lecture_xml = """
    <lecture>
      <title>Introduction to Variables</title>
      <week_number>1</week_number>
      <order_in_week>1</order_in_week>
      <description>Understanding variable concepts</description>
      <content>
        [Professor enters the room]
        Today we'll learn about variables...
      </content>
    </lecture>
    """

    result = parse_lecture_xml(lecture_xml)

    assert result["title"] == "Introduction to Variables"
    assert result["week_number"] == 1
    assert result["order_in_week"] == 1
    assert result["description"] == "Understanding variable concepts"
    assert "Today we'll learn about variables..." in result["content"]

    # Test handling of generate placeholders
    placeholder_xml = """
    <lecture>
      <title>Introduction to Variables</title>
      <week_number>[GENERATE]</week_number>
      <order_in_week>1</order_in_week>
      <description>Understanding variables</description>
      <content>[GENERATE]</content>
    </lecture>
    """

    result = parse_lecture_xml(placeholder_xml)
    assert result["title"] == "Introduction to Variables"
    assert result["week_number"] is None  # [GENERATE] values should be None
    assert result["order_in_week"] == 1
    assert result["description"] == "Understanding variables"
    assert result["content"] is None

    # Test error handling
    with pytest.raises(ValueError):
        parse_lecture_xml("<invalid>XML</with>")


@pytest.mark.unit
def test_extract_xml_content():
    # Test the extract_xml_content function
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
