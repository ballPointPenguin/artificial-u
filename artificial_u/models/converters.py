"""
Functions for converting between database models, dictionaries, and XML formats.
"""

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
        "department_id": professor.department_id,
        "specialization": professor.specialization,
        "background": professor.background,
        "personality": professor.personality,
        "teaching_style": professor.teaching_style,
        "gender": professor.gender,
        "accent": professor.accent,
        "description": professor.description,
        "age": professor.age,
        "voice_id": professor.voice_id,
        "image_url": professor.image_url,
        # Add related fields if needed, e.g., department name after fetching
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
        "department_id": course.department_id,
        "level": course.level,
        "credits": course.credits,
        "professor_id": course.professor_id,
        "description": course.description,
        "lectures_per_week": course.lectures_per_week,
        "total_weeks": course.total_weeks,
        "topics": course.topics,  # Topics might need further processing depending on use case
    }


# --- XML Formatting Functions (mostly for prompts) --- #


def professor_to_xml(
    professor_data: dict, missing_marker: str = "[GENERATE IF NEEDED]"
) -> str:
    """Format professor data (dict) into XML for prompts."""
    if not professor_data:
        # Consistent with format_professor_xml in prompts/courses.py for now
        return "<professor>[GENERATE]</professor>"
    lines = ["<professor>"]
    # Fields relevant for course generation prompt context
    fields = ["name", "title", "specialization", "personality", "teaching_style"]
    for field in fields:
        value = professor_data.get(field)
        if value:
            lines.append(f"  <{field}>{value}</{field}>")
        else:
            lines.append(f"  <{field}>{missing_marker}</{field}>")
    lines.append("</professor>")
    return "\n".join(lines)


def partial_professor_to_xml(
    partial_attrs: Dict[str, Any], missing_marker: str = "[TODO]"
) -> str:
    """Builds the XML string for partial professor attributes (dict), marking missing fields."""
    lines = ["<professor>"]
    # Fields relevant for professor generation prompt context
    fields = [
        "name",
        "title",
        "department_name",  # Note: department_name might not be directly on the model
        "specialization",
        "gender",
        "age",
        "accent",
        "description",
        "background",
        "personality",
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


def professors_to_xml(existing_professors: List[Dict[str, str]]) -> str:
    """Format a list of existing professors (dicts with name, specialization) as XML for prompt context."""
    if not existing_professors:
        return ""
    lines = ["<existing_professors>"]
    for prof in existing_professors:
        lines.append(
            f"  <professor><name>{prof.get('name', 'N/A')}</name>"
            f"<specialization>{prof.get('specialization', 'N/A')}</specialization></professor>"
        )
    lines.append("</existing_professors>")
    return "\n".join(lines)


def department_to_xml(department_data: dict, missing_marker: str = "[MISSING]") -> str:
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


def departments_to_xml(existing_departments: list[str]) -> str:
    """Format a list of department names as XML for prompt context."""
    if not existing_departments:
        return ""
    # Assumes list of names based on prompts/department.py
    return "\n".join(
        f"  <department>{name}</department>" for name in existing_departments
    )


def courses_to_xml(
    existing_courses: List[Dict[str, Any]],
    include_topics: bool = True,
    max_topics: int = 5,
) -> str:
    """Format a list of existing courses (dicts) as XML for context."""
    if not existing_courses:
        return "<no_existing_courses />"

    lines = ["<existing_courses>"]
    for course in existing_courses:
        lines.append("  <course>")
        lines.append(f"    <code>{course.get('code', 'N/A')}</code>")
        lines.append(f"    <title>{course.get('title', 'N/A')}</title>")
        lines.append(
            f"    <description>{course.get('description', 'N/A')}</description>"
        )

        # Add topic overview if available and requested
        course_topics = course.get("topics", [])
        if include_topics and course_topics:
            lines.append("    <topics_overview>")
            topics_to_show = course_topics[:max_topics]
            for topic in topics_to_show:
                # Assuming topics are strings (titles) based on course_service usage
                lines.append(f"      <topic>{topic}</topic>")
            if len(course_topics) > max_topics:
                lines.append(
                    f"      <additional_topics_count>{len(course_topics) - max_topics}</additional_topics_count>"
                )
            lines.append("    </topics_overview>")

        lines.append("  </course>")
    lines.append("</existing_courses>")
    return "\n".join(lines)


def partial_course_to_xml(
    partial_attrs: Dict[str, Any], generate_marker: str = "[GENERATE]"
) -> str:
    """Builds the XML string for partial course attributes (dict), marking missing fields."""
    lines = ["<course>"]
    fields = [
        "code",
        "title",
        "description",
        "level",
        "credits",
        "lectures_per_week",
        "total_weeks",
    ]
    for field in fields:
        value = partial_attrs.get(field)
        if value is not None and value != generate_marker:
            lines.append(f"  <{field}>{str(value)}</{field}>")
        else:
            lines.append(f"  <{field}>{generate_marker}</{field}>")

    # Handle topics section separately
    topics = partial_attrs.get("topics")
    if topics is not None:  # Allow empty list to signify no predefined topics
        lines.append("  <topics>")
        if isinstance(topics, list) and topics:
            # Assumes topics is list of dicts: {"week": w, "lecture": l, "topic": t}
            for topic in topics:
                week = topic.get("week", generate_marker)
                lecture = topic.get("lecture", 1)  # Default to 1 if missing
                topic_text = topic.get("topic", generate_marker)
                lines.append(f'    <week number="{week}">')
                lines.append(f'      <lecture number="{lecture}">')
                lines.append(f"        <topic>{topic_text}</topic>")
                lines.append("      </lecture>")
                lines.append("    </week>")
        else:
            # If topics key exists but is empty or not a list, mark for generation
            lines.append(f"  {generate_marker}")
        lines.append("  </topics>")
    else:
        # If topics key is missing entirely, mark for generation
        lines.append(f"  <topics>{generate_marker}</topics>")

    lines.append("</course>")
    return "\n".join(lines)


# --- XML Parsing Functions --- #


def parse_course_xml(course_xml: str) -> Dict[str, Any]:
    """Parse course XML (typically from LLM response) into a dictionary."""
    try:
        root = ET.fromstring(course_xml)
        course_data = {}
        # Extract simple fields
        for field in [
            "code",
            "title",
            "description",
            "level",
            "credits",
            "lectures_per_week",
            "total_weeks",
        ]:
            element = root.find(field)
            if element is not None and element.text and element.text.strip():
                text_content = element.text.strip()
                if (
                    "[GENERATE]" in text_content
                    or "[TODO]" in text_content
                    or "[MISSING]" in text_content
                ):
                    course_data[field] = None  # Treat markers as null
                else:
                    # Handle potential type conversions
                    if field in ["credits", "lectures_per_week", "total_weeks"]:
                        try:
                            course_data[field] = int(text_content)
                        except (ValueError, TypeError):
                            # Log warning? Decide on handling invalid numbers
                            course_data[field] = None
                    else:
                        course_data[field] = text_content
            else:
                course_data[field] = None

        # Extract topics
        topics_data = []
        topics_root = root.find("topics")
        if topics_root is not None:
            for week_elem in topics_root.findall("week"):
                week_num_str = week_elem.get("number")
                try:
                    week_num = (
                        int(week_num_str)
                        if week_num_str and week_num_str.isdigit()
                        else None
                    )
                except ValueError:
                    week_num = None

                if week_num is not None:
                    for lecture_elem in week_elem.findall("lecture"):
                        lecture_num_str = lecture_elem.get("number")
                        topic_elem = lecture_elem.find("topic")
                        try:
                            lecture_num = (
                                int(lecture_num_str)
                                if lecture_num_str and lecture_num_str.isdigit()
                                else 1
                            )
                        except ValueError:
                            lecture_num = 1

                        if topic_elem is not None and topic_elem.text:
                            topic_text = topic_elem.text.strip()
                            if (
                                topic_text
                                and "[GENERATE]" not in topic_text
                                and "[TODO]" not in topic_text
                            ):
                                topics_data.append(
                                    {
                                        "week_number": week_num,
                                        "order_in_week": lecture_num,
                                        "title": topic_text,
                                    }
                                )
        course_data["topics"] = topics_data

        return course_data
    except ET.ParseError as e:
        # Consider logging here instead of raising immediately
        # Or re-raise a specific parsing error
        raise ValueError(f"Failed to parse course XML: {e}")


# TODO: Implement parse_professor_xml, if needed
# TODO: Implement parse_department_xml, if needed
