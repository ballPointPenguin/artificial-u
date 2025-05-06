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
    lectures_to_xml,
    parse_course_xml,
    parse_department_xml,
    parse_lecture_xml,
    parse_professor_xml,
    parse_topic_xml,
    parse_topics_xml,
    partial_course_to_xml,
    partial_department_to_xml,
    partial_professor_to_xml,
    professor_model_to_dict,
    professor_to_xml,
    professors_to_xml,
    topic_to_xml,
    topics_to_xml,
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

    xml_str = professor_to_xml(partial_data, missing_marker="[GENERATE]")
    root = ET.fromstring(xml_str)
    assert root.find("name").text == "Dr. Jane Smith"
    assert root.find("title").text == "Associate Professor"
    assert root.find("specialization").text == "[GENERATE]"
    assert root.find("personality").text == "[GENERATE]"
    assert root.find("teaching_style").text == "[GENERATE]"


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
    assert departments_to_xml([]) == "<no_existing_departments />"

    # Test with populated list
    departments = [
        {"name": "Computer Science", "code": "CS"},
        {"name": "Mathematics", "code": "MTH"},
        {"name": "Physics", "code": "PHY"},
    ]

    xml_str = departments_to_xml(departments)
    root = ET.fromstring(xml_str)
    assert root.tag == "existing_departments"
    assert len(root) == 3

    depts = root.findall("department")
    assert depts[0].find("name").text == "Computer Science"
    assert depts[0].find("code").text == "CS"


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
        },
        {
            "code": "CS201",
            "title": "Data Structures",
            "description": "Advanced data structures",
        },
    ]

    xml_str = courses_to_xml(courses)
    root = ET.fromstring(xml_str)
    assert root.tag == "existing_courses"
    assert len(root) == 2

    course_elems = root.findall("course")

    # Check first course
    assert course_elems[0].find("code").text == "CS101"
    assert course_elems[0].find("title").text == "Introduction to Programming"
    assert course_elems[0].find("description").text == "Basic programming concepts"

    # Check second course
    assert course_elems[1].find("code").text == "CS201"
    assert course_elems[1].find("title").text == "Data Structures"
    assert course_elems[1].find("description").text == "Advanced data structures"


@pytest.mark.unit
def test_partial_course_to_xml():
    """Test converting partial course attributes to XML."""
    # Test with empty data
    empty_xml = partial_course_to_xml({})
    root = ET.fromstring(empty_xml)
    assert root.tag == "course"
    assert len(root.findall("*")) == 7  # 7 fields

    # Test with partial data
    partial_data = {
        "code": "CS101",
        "title": "Introduction to Programming",
        "description": "Basic programming concepts",
        "level": "Undergraduate",
    }

    xml_str = partial_course_to_xml(partial_data)
    root = ET.fromstring(xml_str)
    assert root.find("code").text == "CS101"
    assert root.find("title").text == "Introduction to Programming"
    assert root.find("description").text == "Basic programming concepts"
    assert root.find("level").text == "Undergraduate"
    assert root.find("credits").text == "[GENERATE]"


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
def test_lectures_to_xml():
    """Test converting a list of lectures to XML."""
    # Test with empty list
    assert lectures_to_xml([]) == "<no_existing_lectures />"

    # Test with populated list
    lectures = [
        {
            "week": 1,
            "order": 1,
            "title": "Introduction to Variables",
            "summary": "Understanding basic variable concepts",
        },
        {
            "week": 1,
            "order": 2,
            "title": "Control Flow",
            "summary": "Understanding loops and conditionals",
        },
    ]

    xml_str = lectures_to_xml(lectures)
    root = ET.fromstring(xml_str)
    assert root.tag == "existing_lectures"
    assert len(root.findall("lecture")) == 2

    lecture_elems = root.findall("lecture")
    assert lecture_elems[0].find("week").text == "1"
    assert lecture_elems[0].find("order").text == "1"
    assert lecture_elems[0].find("topic").text == "Introduction to Variables"
    assert lecture_elems[0].find("summary").text == "Understanding basic variable concepts"


@pytest.mark.unit
def test_topic_to_xml():
    """Test converting a topic to XML."""
    # Test with empty data
    with pytest.raises(ValueError):
        topic_to_xml({})

    # Test with missing required fields
    with pytest.raises(ValueError):
        topic_to_xml({"title": "Introduction to Variables"})

    # Test with populated data
    topic_data = {
        "title": "Introduction to Variables",
        "week": 1,
        "order": 1,
    }

    xml_str = topic_to_xml(topic_data)
    root = ET.fromstring(xml_str)
    assert root.tag == "topic"
    assert root.find("title").text == "Introduction to Variables"
    assert root.find("week").text == "1"
    assert root.find("order").text == "1"


@pytest.mark.unit
def test_topics_to_xml():
    """Test converting a list of topics to XML."""
    # Test with empty list
    assert topics_to_xml([]) == "<no_existing_topics />"

    # Test with populated list
    topics = [
        {
            "title": "Introduction to Variables",
            "week": 1,
            "order": 1,
        },
        {
            "title": "Control Flow",
            "week": 1,
            "order": 2,
        },
    ]

    xml_str = topics_to_xml(topics)
    root = ET.fromstring(xml_str)
    assert root.tag == "topics"
    assert len(root.findall("topic")) == 2

    topic_elems = root.findall("topic")
    assert topic_elems[0].find("title").text == "Introduction to Variables"
    assert topic_elems[0].find("week").text == "1"
    assert topic_elems[0].find("order").text == "1"

    # Test with max_topics limit
    xml_str = topics_to_xml(topics, max_topics=1)
    root = ET.fromstring(xml_str)
    assert len(root.findall("topic")) == 1
    assert root.find("additional_topics_count").text.strip() == "1"


@pytest.mark.unit
def test_parse_topic_xml():
    """Test parsing topic XML into a dictionary."""
    # Create a valid topic XML
    topic_xml = """
    <topic>
      <title>Introduction to Variables</title>
      <week>1</week>
      <order>1</order>
    </topic>
    """

    result = parse_topic_xml(topic_xml)

    assert result["title"] == "Introduction to Variables"
    assert result["week"] == 1
    assert result["order"] == 1

    # Test error handling
    with pytest.raises(ValueError):
        parse_topic_xml("<invalid>XML</with>")


@pytest.mark.unit
def test_parse_topics_xml():
    """Test parsing topics XML into a list of dictionaries."""
    # Create a valid topics XML
    topics_xml = """
    <topics>
      <topic>
        <title>Introduction to Variables</title>
        <week>1</week>
        <order>1</order>
      </topic>
      <topic>
        <title>Control Flow</title>
        <week>1</week>
        <order>2</order>
      </topic>
    </topics>
    """

    result = parse_topics_xml(topics_xml)

    assert len(result) == 2
    assert result[0]["title"] == "Introduction to Variables"
    assert result[0]["week"] == 1
    assert result[0]["order"] == 1
    assert result[1]["title"] == "Control Flow"
    assert result[1]["week"] == 1
    assert result[1]["order"] == 2

    # Test error handling
    with pytest.raises(ValueError):
        parse_topics_xml("<invalid>XML</with>")


@pytest.mark.unit
def test_parse_professor_xml():
    """Test parsing professor XML into a dictionary."""
    # Create a valid professor XML
    professor_xml = """
    <professor>
      <name>Dr. Jane Smith</name>
      <title>Associate Professor</title>
      <accent>American</accent>
      <age>35</age>
      <background>PhD from Stanford</background>
      <description>Expert in Machine Learning</description>
      <gender>Female</gender>
      <personality>Engaging</personality>
      <specialization>Machine Learning</specialization>
      <teaching_style>Interactive</teaching_style>
    </professor>
    """

    result = parse_professor_xml(professor_xml)

    assert result["name"] == "Dr. Jane Smith"
    assert result["title"] == "Associate Professor"
    assert result["accent"] == "American"
    assert result["age"] == 35
    assert result["background"] == "PhD from Stanford"
    assert result["description"] == "Expert in Machine Learning"
    assert result["gender"] == "Female"
    assert result["personality"] == "Engaging"
    assert result["specialization"] == "Machine Learning"
    assert result["teaching_style"] == "Interactive"

    # Test error handling
    with pytest.raises(ValueError):
        parse_professor_xml("<invalid>XML</with>")


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


@pytest.mark.unit
def test_parse_department_xml():
    """Test parsing department XML into a dictionary."""
    # Create a valid department XML
    department_xml = """
    <department>
      <name>Computer Science</name>
      <code>CS</code>
      <faculty>Science and Engineering</faculty>
      <description>Study of computation and software systems</description>
    </department>
    """

    result = parse_department_xml(department_xml)

    assert result["name"] == "Computer Science"
    assert result["code"] == "CS"
    assert result["faculty"] == "Science and Engineering"
    assert result["description"] == "Study of computation and software systems"

    # Test error handling for invalid XML
    with pytest.raises(ValueError) as exc_info:
        parse_department_xml("<invalid>XML</with>")
    assert "Invalid XML format" in str(exc_info.value)


@pytest.mark.unit
def test_partial_department_to_xml():
    """Test converting partial department attributes to XML."""
    # Test with empty data
    empty_xml = partial_department_to_xml({})
    root = ET.fromstring(empty_xml)
    assert root.tag == "department"
    assert len(root.findall("*")) == 4  # All fields should be present with [GENERATE]

    # Test with partial data
    partial_data = {
        "name": "Computer Science",
        "code": "CS",
        "faculty": "Science and Engineering",
    }

    xml_str = partial_department_to_xml(partial_data)
    root = ET.fromstring(xml_str)
    assert root.find("name").text == "Computer Science"
    assert root.find("code").text == "CS"
    assert root.find("faculty").text == "Science and Engineering"
    assert root.find("description").text == "[GENERATE]"

    # Test with custom generate marker
    xml_str = partial_department_to_xml(partial_data, generate_marker="[TODO]")
    root = ET.fromstring(xml_str)
    assert root.find("description").text == "[TODO]"

    # Test with all fields provided
    complete_data = {
        "name": "Computer Science",
        "code": "CS",
        "faculty": "Science and Engineering",
        "description": "Study of computation",
    }

    xml_str = partial_department_to_xml(complete_data)
    root = ET.fromstring(xml_str)
    assert root.find("name").text == "Computer Science"
    assert root.find("code").text == "CS"
    assert root.find("faculty").text == "Science and Engineering"
    assert root.find("description").text == "Study of computation"


@pytest.mark.unit
def test_parse_lecture_xml():
    """Test parsing lecture XML into a dictionary."""
    # Create a valid lecture XML
    lecture_xml = """
    <lecture>
      <content>Today we'll learn about variables...</content>
    </lecture>
    """

    result = parse_lecture_xml(lecture_xml)

    assert result["content"] == "Today we'll learn about variables..."

    # Test error handling
    with pytest.raises(ValueError):
        parse_lecture_xml("<invalid>XML</with>")
