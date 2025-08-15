"""
Functions for converting between database models, dictionaries, and XML formats.
"""

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from artificial_u.models.core import Course, Department, Lecture, Professor, Topic

# --- Model to Dict Converters --- #


def professor_model_to_dict(professor: Optional[Professor]) -> Dict[str, Any]:
    """Convert Professor Pydantic model to dictionary."""
    if not professor:
        return {}
    return professor.model_dump(exclude_none=True)


def department_model_to_dict(department: Optional[Department]) -> Dict[str, Any]:
    """Convert Department Pydantic model to dictionary."""
    if not department:
        return {}
    return department.model_dump(exclude_none=True)


def course_model_to_dict(course: Optional[Course]) -> Dict[str, Any]:
    """Convert Course Pydantic model to dictionary."""
    if not course:
        return {}
    return course.model_dump(exclude_none=True)


def lecture_model_to_dict(lecture: Optional[Lecture]) -> Dict[str, Any]:
    """Convert Lecture Pydantic model to dictionary."""
    if not lecture:
        return {}
    return lecture.model_dump(exclude_none=True)


def topic_model_to_dict(topic: Optional[Topic]) -> Dict[str, Any]:
    """Convert a Topic Pydantic model to a dictionary."""
    if not topic:
        return {}
    return topic.model_dump(exclude_none=True)


def topics_model_to_dict(topics: List[Topic]) -> List[Dict[str, Any]]:
    """Convert a list of Topic Pydantic models to a list of dictionaries."""
    if not topics:
        return []
    return [topic.model_dump(exclude_none=True) for topic in topics]


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
    # Format a list of professors (dicts with id, name, title, specialization)
    # as XML for prompt context.
    if not professors:
        return "<no_existing_professors />"
    lines = ["<existing_professors>"]
    for prof in professors:
        lines.append(
            f"  <professor><id>{prof.get('id', '')}</id>"
            f"<name>{prof.get('name', '')}</name>"
            f"<title>{prof.get('title', '')}</title>"
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
        departments: List of department dictionaries containing 'id', 'name',
                    'code', and 'faculty' keys.
    """
    if not departments:
        return "<no_existing_departments />"
    lines = ["<existing_departments>"]
    for dept in departments:
        lines.append("  <department>")
        lines.append(f"    <id>{dept.get('id', '')}</id>")
        lines.append(f"    <name>{dept.get('name', '')}</name>")
        lines.append(f"    <code>{dept.get('code', '')}</code>")
        lines.append(f"    <faculty>{dept.get('faculty', '')}</faculty>")
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

    # Add content if present
    content = topic.get("content")
    if content:
        content_xml = _content_json_to_xml(content, "  ")
        lines.append(content_xml)

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

        # Add content if present
        content = topic.get("content")
        if content:
            content_xml = _content_json_to_xml(content, "    ")
            lines.append(content_xml)

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
        lines.append(f"    <title>{lecture.get('title', '')}</title>")
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


def _content_json_to_xml(content: Optional[Dict[str, Any]], indent: str = "  ") -> str:
    """Convert content JSON to XML format for LLM prompts.

    Two simple patterns:
    - Single: {"lecture": "text"} → <lecture>text</lecture>
    - List: {"readings": ["a", "b"]} → <readings><reading>a</reading><reading>b</reading></readings>
    """
    if not content:
        return ""

    lines = [f"{indent}<content>"]

    for key, value in content.items():
        if isinstance(value, str):
            # Single item pattern
            lines.append(f"{indent}  <{key}>{value}</{key}>")
        elif isinstance(value, list):
            # Simple list pattern - convert plural to singular (readings -> reading)
            singular_key = key[:-1] if key.endswith("s") else key
            lines.append(f"{indent}  <{key}>")
            for item in value:
                lines.append(f"{indent}    <{singular_key}>{item}</{singular_key}>")
            lines.append(f"{indent}  </{key}>")

    lines.append(f"{indent}</content>")
    return "\n".join(lines)


def _content_xml_to_json(content_element: Optional[ET.Element]) -> Optional[Dict[str, Any]]:
    """Convert content XML element to JSON format.

    Supports two simple patterns:
    - Single item: <lecture>text</lecture> → {"lecture": "text"}
    - Simple list: <readings><reading>text1</reading><reading>text2</reading></readings>
      → {"readings": ["text1", "text2"]}
    """
    if content_element is None:
        return None

    content = {}

    for child in content_element:
        tag = child.tag

        if len(child) == 0:  # Leaf node with text - single item pattern
            text = child.text.strip() if child.text else ""
            if text:
                content[tag] = text
        else:  # Has child elements - simple list pattern
            items = []
            for subchild in child:
                sub_text = subchild.text.strip() if subchild.text else ""
                if sub_text:
                    items.append(sub_text)
            if items:
                content[tag] = items

    return content if content else None


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

        # Process content field
        content_element = root.find("content")
        topic_data["content"] = _content_xml_to_json(content_element)

        return topic_data

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")


def _repair_topics_xml(xml_str: str) -> str:
    """Repair common XML issues in topics XML.

    Args:
        xml_str: The potentially malformed XML string

    Returns:
        str: Repaired XML string
    """
    import html
    import re

    # Fix common mismatched closing tags
    # Special case: <order>X</content> means close order AND open content
    def fix_mismatched_tags(text):
        """Fix mismatched closing tags."""
        # First handle the special case where </content> is used to close order AND open content
        text = re.sub(r"(\s*)<order>(\d+)</content>", r"\1<order>\2</order>\n\1<content>", text)

        # Then handle other common mismatches
        patterns = [
            (r"<week>(\d+)</content>", r"<week>\1</week>"),
            (r"<order>(\d+)</week>", r"<order>\1</order>"),
            (r"<week>(\d+)</order>", r"<week>\1</week>"),
        ]
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    xml_str = fix_mismatched_tags(xml_str)

    # Then escape problematic characters within text content
    # We need to be careful to only escape content, not XML tags themselves
    def escape_xml_content(match):
        """Escape special characters in XML text content."""
        content = match.group(1)
        # Only escape if it contains problematic characters
        if any(c in content for c in ["&", "<", ">", '"', "'"]):
            # Don't double-escape already escaped content
            if not re.search(r"&[a-zA-Z]+;|&#\d+;", content):
                content = html.escape(content, quote=False)
        return f">{content}<"

    # Escape content between XML tags (but not the tags themselves)
    # This pattern matches >content< where content doesn't contain < or >
    xml_str = re.sub(r">([^<>]+)<", escape_xml_content, xml_str)

    # Fix missing </content> tags before </topic>
    # This is a common issue where LLMs forget to close content tags
    lines = xml_str.split("\n")
    repaired_lines = []
    in_content = False

    for i, line in enumerate(lines):
        # Track when we enter a content tag
        if "<content>" in line:
            in_content = True
            repaired_lines.append(line)
        # If we see </content>, we're no longer in content
        elif "</content>" in line:
            in_content = False
            repaired_lines.append(line)
        # If we see </topic> while still in content, add missing </content>
        elif "</topic>" in line and in_content:
            # Add proper indentation based on the </topic> line
            indent = len(line) - len(line.lstrip())
            repaired_lines.append(" " * (indent + 2) + "</content>")
            repaired_lines.append(line)
            in_content = False
        else:
            repaired_lines.append(line)

    return "\n".join(repaired_lines)


def parse_topics_xml(topics_xml: str) -> List[Dict[str, Any]]:
    """Parse topics XML from LLM response into a list of dictionaries.

    Args:
        topics_xml: The XML string to parse

    Returns:
        List[Dict[str, Any]]: A list of parsed topic dictionaries

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    # First, try to repair common XML issues
    topics_xml = _repair_topics_xml(topics_xml)

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


def _repair_lecture_xml(xml_str: str) -> str:
    """Repair common XML issues in lecture XML.

    Args:
        xml_str: The potentially malformed XML string

    Returns:
        str: Repaired XML string
    """
    import html

    # Fix common HTML entities that might not be properly escaped
    xml_str = xml_str.replace("&amp;", "&")  # Temporarily simplify
    xml_str = html.escape(xml_str, quote=False)  # Re-escape properly

    # Fix common unclosed tags by ensuring proper nesting
    # Count opening and closing tags
    title_open = xml_str.count("<title>")
    title_close = xml_str.count("</title>")
    content_open = xml_str.count("<content>")
    content_close = xml_str.count("</content>")

    # Add missing closing tags
    if title_open > title_close:
        # Find position to insert </title> - before <content> or at end
        content_pos = xml_str.find("<content>")
        if content_pos > 0:
            xml_str = xml_str[:content_pos] + "</title>" + xml_str[content_pos:]
        else:
            xml_str = xml_str.replace("</lecture>", "</title></lecture>")

    if content_open > content_close:
        # Add missing </content> before </lecture>
        xml_str = xml_str.replace("</lecture>", "</content></lecture>")

    return xml_str


def _extract_lecture_xml_portion(lecture_xml: str) -> str:
    """Extract the <lecture>...</lecture> portion from the response.

    Args:
        lecture_xml: The full XML response that may contain extra content

    Returns:
        str: Just the lecture XML portion

    Raises:
        ValueError: If lecture tags are not found or malformed
    """
    lecture_start = lecture_xml.find("<lecture>")
    lecture_end = lecture_xml.find("</lecture>")

    if lecture_start == -1:
        raise ValueError("No <lecture> opening tag found in response")
    if lecture_end == -1:
        # Maybe the closing tag is malformed, try to find partial
        lecture_end = lecture_xml.find("</lectur")
        if lecture_end == -1:
            raise ValueError("No </lecture> closing tag found in response")
        # Adjust to include the full closing tag
        lecture_end = lecture_xml.find(">", lecture_end)

    if lecture_end <= lecture_start:
        raise ValueError("Invalid lecture tag structure")

    # Extract just the lecture XML portion
    lecture_only_xml = lecture_xml[lecture_start : lecture_end + 1]
    if not lecture_only_xml.endswith("</lecture>"):
        lecture_only_xml = lecture_only_xml.replace("</lectur", "</lecture")
        if not lecture_only_xml.endswith(">"):
            lecture_only_xml += ">"

    return lecture_only_xml


def _parse_lecture_xml_with_et(lecture_only_xml: str) -> Dict[str, Any]:
    """Parse lecture XML using ElementTree.

    Args:
        lecture_only_xml: The cleaned lecture XML portion

    Returns:
        Dict[str, Any]: Parsed lecture data

    Raises:
        ET.ParseError: If XML parsing fails
        ValueError: If structure is invalid
    """
    # Try to parse as-is first
    try:
        root = ET.fromstring(lecture_only_xml.strip())
    except ET.ParseError:
        # Try to repair common issues
        lecture_only_xml = _repair_lecture_xml(lecture_only_xml)
        root = ET.fromstring(lecture_only_xml.strip())

    # The root element should be the lecture
    if root.tag != "lecture":
        raise ValueError("Root element must be <lecture>")

    lecture_data = {}

    # Process title and content fields
    lecture_data["title"] = _parse_text_field(root.find("title"))
    lecture_data["content"] = _parse_text_field(root.find("content"))

    return lecture_data


def _parse_lecture_xml_with_regex(lecture_xml: str) -> Dict[str, Any]:
    """Parse lecture XML using regex as a fallback strategy.

    Args:
        lecture_xml: The full XML response

    Returns:
        Dict[str, Any]: Parsed lecture data

    Raises:
        ValueError: If no content could be extracted
    """
    import html
    import re

    lecture_data = {}

    # Try to extract title with regex (handle unclosed tags)
    title_match = re.search(
        r"<title>\s*(.*?)(?:</title>|<content>|</lecture>)",
        lecture_xml,
        re.DOTALL | re.IGNORECASE,
    )
    if title_match:
        title = title_match.group(1).strip()
        # Unescape any HTML entities
        title = html.unescape(title)
        lecture_data["title"] = title

    # Try to extract content with regex (handle unclosed tags)
    content_match = re.search(
        r"<content>\s*(.*?)(?:</content>|</lecture>|$)", lecture_xml, re.DOTALL | re.IGNORECASE
    )

    if content_match:
        content = content_match.group(1).strip()
        # Unescape any HTML entities
        content = html.unescape(content)
        lecture_data["content"] = content

    # If we got at least content, consider it a success
    if lecture_data.get("content"):
        return lecture_data

    raise ValueError("Could not extract content using regex fallback")


def parse_lecture_xml(lecture_xml: str) -> Dict[str, Any]:
    """Parse lecture XML from LLM response into a dictionary.

    This function is robust and extracts only the <lecture> portion from the response,
    ignoring any content before or after the lecture tags (like outlines or other text).
    It also attempts to repair common XML issues.

    Args:
        lecture_xml: The XML string to parse (may contain extra content)

    Returns:
        Dict[str, Any]: The parsed lecture attributes

    Raises:
        ValueError: If the XML is invalid or missing required elements
    """
    # Strategy 1: Try to extract and parse clean XML
    try:
        lecture_only_xml = _extract_lecture_xml_portion(lecture_xml)
        return _parse_lecture_xml_with_et(lecture_only_xml)
    except (ET.ParseError, ValueError) as e:
        # Strategy 2: Try regex-based extraction as fallback
        try:
            return _parse_lecture_xml_with_regex(lecture_xml)
        except ValueError:
            # If all strategies failed, raise the original error
            raise ValueError(f"Could not parse lecture XML: {e}")
