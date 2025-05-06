"""
Functions for converting between database models, dictionaries, and XML formats.
"""

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from artificial_u.models.database import CourseModel, DepartmentModel, ProfessorModel

# --- Model to Dict Converters --- #


def professor_model_to_dict(professor: Optional[ProfessorModel]) -> Dict[str, Any]:
    """Convert ProfessorModel to dictionary."""
    if not professor:
        return {}
    return {
        "id": professor.id,
        "name": professor.name,
        "title": professor.title,
        "accent": professor.accent,
        "age": professor.age,
        "background": professor.background,
        "description": professor.description,
        "gender": professor.gender,
        "personality": professor.personality,
        "specialization": professor.specialization,
        "teaching_style": professor.teaching_style,
        "image_url": professor.image_url,
        "department_id": professor.department_id,
        "voice_id": professor.voice_id,
    }


def department_model_to_dict(department: Optional[DepartmentModel]) -> Dict[str, Any]:
    """Convert DepartmentModel to dictionary."""
    if not department:
        return {}
    return {
        "id": department.id,
        "name": department.name,
        "code": department.code,
        "faculty": department.faculty,
        "description": department.description,
    }


def course_model_to_dict(course: Optional[CourseModel]) -> Dict[str, Any]:
    """Convert CourseModel to dictionary."""
    if not course:
        return {}
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "credits": course.credits,
        "description": course.description,
        "lectures_per_week": course.lectures_per_week,
        "level": course.level,
        "total_weeks": course.total_weeks,
        "department_id": course.department_id,
        "professor_id": course.professor_id,
    }


# --- XML Formatting Functions (mostly for prompts) --- #


def professor_to_xml(professor_data: dict, missing_marker: str = "[GENERATE]") -> str:
    """Format professor data (dict) into XML for prompts."""
    if not professor_data:
        # Consistent with format_professor_xml in prompts/courses.py for now
        return "<professor>[GENERATE]</professor>"
    lines = ["<professor>"]
    # Fields relevant for course generation prompt context
    fields = [
        "name",
        "title",
        "accent",
        "age",
        "background",
        "description",
        "gender",
        "personality",
        "specialization",
        "teaching_style",
    ]
    for field in fields:
        value = professor_data.get(field)
        if value:
            lines.append(f"  <{field}>{value}</{field}>")
        else:
            lines.append(f"  <{field}>{missing_marker}</{field}>")
    lines.append("</professor>")
    return "\n".join(lines)


def partial_professor_to_xml(
    partial_attrs: Dict[str, Any], missing_marker: str = "[GENERATE]"
) -> str:
    """Builds the XML string for partial professor attributes (dict), marking missing fields."""
    lines = ["<professor>"]
    # Fields relevant for professor generation prompt context
    fields = [
        "name",
        "title",
        "department_name",  # Note: department_name might not be directly on the model
        "accent",
        "age",
        "background",
        "description",
        "gender",
        "personality",
        "specialization",
        "teaching_style",
    ]
    for field in fields:
        value = partial_attrs.get(field)
        if value is not None:
            lines.append(f"  <{field}>{str(value)}</{field}>")
        else:
            lines.append(f"  <{field}>{missing_marker}</{field}>")
    lines.append("</professor>")
    return "\n".join(lines)


def professors_to_xml(professors: List[Dict[str, str]]) -> str:
    # Format a list of professors (dicts with name, specialization)
    # as XML for prompt context.
    if not professors:
        return "<no_existing_professors />"
    lines = ["<existing_professors>"]
    for prof in professors:
        lines.append(
            f"  <professor><name>{prof.get('name', '')}</name>"
            f"<specialization>{prof.get('specialization', '')}</specialization></professor>"
        )
    lines.append("</existing_professors>")
    return "\n".join(lines)


def department_to_xml(department_data: dict, missing_marker: str = "[GENERATE]") -> str:
    """Format department data (dict) into XML for prompts."""
    if not department_data:
        # Consistent with format_department_xml in prompts/courses.py
        return "<department>[GENERATE]</department>"
    lines = ["<department>"]
    # Fields relevant for course generation prompt context
    fields = ["name", "code", "faculty", "description"]
    for field in fields:
        value = department_data.get(field)
        if value:
            lines.append(f"  <{field}>{value}</{field}>")
        else:
            lines.append(f"  <{field}>{missing_marker}</{field}>")
    lines.append("</department>")
    return "\n".join(lines)


def departments_to_xml(departments: List[Dict[str, str]]) -> str:
    """Format a list of department dictionaries as XML for prompt context.

    Args:
        departments: List of department dictionaries containing 'name' and 'code' keys.
    """
    if not departments:
        return "<no_existing_departments />"
    lines = ["<existing_departments>"]
    for dept in departments:
        lines.append("  <department>")
        lines.append(f"    <name>{dept.get('name', '')}</name>")
        lines.append(f"    <code>{dept.get('code', '')}</code>")
        lines.append("  </department>")
    lines.append("</existing_departments>")
    return "\n".join(lines)


def partial_course_to_xml(
    partial_attrs: Dict[str, Any], generate_marker: str = "[GENERATE]"
) -> str:
    """Builds the XML string for partial course attributes (dict), marking missing fields."""
    lines = ["<course>"]
    fields = [
        "code",
        "title",
        "credits",
        "description",
        "lectures_per_week",
        "level",
        "total_weeks",
    ]
    for field in fields:
        value = partial_attrs.get(field)
        if value is not None and value != generate_marker:
            lines.append(f"  <{field}>{str(value)}</{field}>")
        else:
            lines.append(f"  <{field}>{generate_marker}</{field}>")

    lines.append("</course>")
    return "\n".join(lines)


def courses_to_xml(courses: List[Dict[str, Any]]) -> str:
    """Format a list of courses (dicts) as XML for context."""
    if not courses:
        return "<no_existing_courses />"

    lines = ["<existing_courses>"]
    for course in courses:
        lines.append("  <course>")
        lines.append(f"    <code>{course.get('code', '')}</code>")
        lines.append(f"    <title>{course.get('title', '')}</title>")
        lines.append(f"    <description>{course.get('description', '')}</description>")
        lines.append("  </course>")
    lines.append("</existing_courses>")
    return "\n".join(lines)


def topic_to_xml(topic: Dict[str, Any]) -> str:
    """Format a topic (dict) as XML for context."""

    if not topic:
        raise ValueError("Topic data is required")

    for key in ["title", "week", "order"]:
        if key not in topic:
            raise ValueError(f"Required field '{key}' is missing or empty")

    lines = ["<topic>"]
    lines.append(f"  <title>{topic.get('title', '')}</title>")
    lines.append(f"  <week>{topic.get('week', '')}</week>")
    lines.append(f"  <order>{topic.get('order', '')}</order>")
    lines.append("</topic>")
    return "\n".join(lines)


def topics_to_xml(topics: List[Dict[str, Any]], max_topics: int = 5) -> str:
    """Format a list of topics as XML for context."""
    if not topics:
        return "<no_existing_topics />"

    lines = ["<topics>"]
    for topic in topics[:max_topics]:
        lines.append("  <topic>")
        lines.append(f"    <title>{topic.get('title', '')}</title>")
        if topic.get("week") is not None:
            lines.append(f"    <week>{topic.get('week')}</week>")
        if topic.get("order") is not None:
            lines.append(f"    <order>{topic.get('order')}</order>")
        lines.append("  </topic>")

    if len(topics) > max_topics:
        lines.append(
            f"  <additional_topics_count>"
            f"    {len(topics) - max_topics}"
            f"  </additional_topics_count>"
        )

    lines.append("</topics>")
    return "\n".join(lines)


def lectures_to_xml(lectures: List[Dict[str, Any]]) -> str:
    """Format a list of lecture related attributes as XML for context."""
    if not lectures:
        return "<no_existing_lectures />"

    lines = ["<existing_lectures>"]
    for lecture in lectures:
        lines.append("  <lecture>")
        lines.append(f"    <week>{lecture.get('week', '')}</week>")
        lines.append(f"    <order>{lecture.get('order', '')}</order>")
        lines.append(f"    <topic>{lecture.get('title', '')}</topic>")
        lines.append(f"    <summary>{lecture.get('summary', '')}</summary>")
        lines.append("  </lecture>")
    lines.append("</existing_lectures>")
    return "\n".join(lines)


def partial_department_to_xml(
    partial_attrs: Dict[str, Any], generate_marker: str = "[GENERATE]"
) -> str:
    """Builds the XML string for partial department attributes, marking missing fields.

    Args:
        partial_attrs: Dictionary of known department attributes
        generate_marker: Marker to use for missing fields

    Returns:
        str: XML representation of the department
    """
    lines = ["<department>"]
    fields = ["name", "code", "faculty", "description"]
    for field in fields:
        value = partial_attrs.get(field)
        if value is not None and value != generate_marker:
            lines.append(f"  <{field}>{str(value)}</{field}>")
        else:
            lines.append(f"  <{field}>{generate_marker}</{field}>")
    lines.append("</department>")
    return "\n".join(lines)


# --- XML Parsing Functions --- #


def extract_xml_content(text: str, tag_name: str) -> Optional[str]:
    """Extract content from XML tags.

    Args:
        text: Text containing XML tags
        tag_name: The name of the XML tag to extract

    Returns:
        Optional[str]: Extracted content or None if not found
    """
    pattern = rf"<{tag_name}>\s*(.*?)\s*</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)

    return match.group(1).strip() if match else None


def _parse_text_field(element: Optional[ET.Element]) -> Optional[str]:
    """Parse a simple text field from an Element."""
    if element is not None and element.text:
        value = element.text.strip()
        return None if "[GENERATE]" in value else value
    return None


def _parse_numeric_field(element: Optional[ET.Element]) -> Optional[int]:
    """Parse a numeric field from an Element."""
    if element is not None and element.text:
        value = element.text.strip()
        if "[GENERATE]" in value:
            return None
        try:
            return int(value)
        except ValueError:
            return None
    return None


def parse_course_xml(course_xml: str) -> Dict[str, Any]:
    """Parse course XML from LLM response into a dictionary.

    Args:
        course_xml: The XML string to parse

    Returns:
        Dict[str, Any]: The parsed course attributes

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    try:
        root = ET.fromstring(course_xml)
        course_data = {}

        # Process simple text fields
        for field in ["code", "title", "description", "level"]:
            course_data[field] = _parse_text_field(root.find(field))

        # Process numeric fields
        for field in ["credits", "lectures_per_week", "total_weeks"]:
            course_data[field] = _parse_numeric_field(root.find(field))

        return course_data

    except ET.ParseError as e:
        raise ValueError(f"Failed to parse course XML: {e}")
    except Exception as e:
        raise ValueError(f"Error processing course data: {e}")


def parse_topic_xml(topic_xml: str) -> Dict[str, Any]:
    """Parse topic XML from LLM response into a dictionary.

    Args:
        topic_xml: The XML string to parse

    Returns:
        Dict[str, Any]: The parsed topic attributes

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    try:
        root = ET.fromstring(topic_xml.strip())
        # The root element should be the topic
        if root.tag != "topic":
            raise ValueError("Root element must be <topic>")

        topic_data = {}

        # Process simple text fields
        topic_data["title"] = _parse_text_field(root.find("title"))
        topic_data["week"] = _parse_numeric_field(root.find("week"))
        topic_data["order"] = _parse_numeric_field(root.find("order"))

        return topic_data

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")


def parse_topics_xml(topics_xml: str) -> List[Dict[str, Any]]:
    """Parse topics XML from LLM response into a list of dictionaries.

    Args:
        topics_xml: The XML string to parse

    Returns:
        List[Dict[str, Any]]: A list of parsed topic dictionaries

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    try:
        root = ET.fromstring(topics_xml.strip())
        # The root element should be the topics
        if root.tag != "topics":
            raise ValueError("Root element must be <topics>")

        topics_data = []

        # Process each topic element
        for topic in root.findall("topic"):
            topic_data = parse_topic_xml(ET.tostring(topic, encoding="utf-8").decode())
            topics_data.append(topic_data)

        return topics_data

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing topics XML: {e}")


def parse_department_xml(department_xml: str) -> Dict[str, Any]:
    """Parse department XML from LLM response into a dictionary.

    Args:
        department_xml: The XML string to parse

    Returns:
        Dict[str, Any]: The parsed department attributes

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    try:
        root = ET.fromstring(department_xml.strip())
        # The root element should be the department
        if root.tag != "department":
            raise ValueError("Root element must be <department>")

        department_data = {}

        # Process simple text fields
        for field in ["name", "code", "faculty", "description"]:
            department_data[field] = _parse_text_field(root.find(field))

        return department_data

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing department XML: {e}")


def parse_professor_xml(professor_xml: str) -> Dict[str, Any]:
    """Parse professor XML from LLM response into a dictionary.

    Args:
        professor_xml: The XML string to parse

    Returns:
        Dict[str, Any]: The parsed professor attributes

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    try:
        root = ET.fromstring(professor_xml.strip())
        # The root element should be the professor
        if root.tag != "professor":
            raise ValueError("Root element must be <professor>")

        professor_data = {}

        # Process simple text fields
        for field in [
            "name",
            "title",
            "accent",
            "background",
            "description",
            "gender",
            "personality",
            "specialization",
            "teaching_style",
        ]:
            professor_data[field] = _parse_text_field(root.find(field))

        # Process numeric fields
        professor_data["age"] = _parse_numeric_field(root.find("age"))

        return professor_data

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing professor XML: {e}")


def parse_lecture_xml(lecture_xml: str) -> Dict[str, Any]:
    """Parse lecture XML from LLM response into a dictionary.

    Args:
        lecture_xml: The XML string to parse

    Returns:
        Dict[str, Any]: The parsed lecture attributes

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    try:
        root = ET.fromstring(lecture_xml.strip())
        # The root element should be the lecture
        if root.tag != "lecture":
            raise ValueError("Root element must be <lecture>")

        lecture_data = {}

        # Process content field
        lecture_data["content"] = _parse_text_field(root.find("content"))

        return lecture_data

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing lecture XML: {e}")
