"""Course selection prompt templates for quickstart wizard."""

from typing import Any, Dict, List

from artificial_u.prompts.base import PromptTemplate

# XML structure for course selection decision
COURSE_SELECTION_STRUCTURE = """
<decision>
  <action>[SELECT|GENERATE]</action>
  <course_ids>[comma-separated IDs or empty]</course_ids>
  <reasoning>[Detailed explanation]</reasoning>
</decision>
"""

# Course selection prompt
COURSE_SELECTION_PROMPT = PromptTemplate(
    template="""
You are helping a student find courses to learn from at an AI-powered university.

The student has expressed their learning goal:
<learning_goal>
{user_query}
</learning_goal>

Here are the currently available published courses:
{courses_xml}

Your task is to decide whether to:
1. SELECT: Recommend 1-3 existing courses that match the student's learning goal
2. GENERATE: Signal that a new course should be created (if no existing courses are a good match)

Decision Criteria:
- Topic relevance: Does the course content align with what the student wants to learn?
- Specificity match: Is the course at the right level of specificity for their goal?
- Quality of fit: Would this course genuinely help them learn what they're asking about?

If SELECTING existing courses:
- Choose up to 3 courses that best match the learning goal
- Only include courses that are genuinely relevant (don't pad with weak matches)
- Use the numeric IDs from the courses list above
- Explain why each selected course is a good fit

If GENERATING a new course:
- Only choose this if no existing courses are reasonably relevant
- Explain what kind of course would better serve the student's needs

Output Format:
{course_selection_structure}

Example - Selecting existing courses:
<decision>
  <action>SELECT</action>
  <course_ids>15, 23</course_ids>
  <reasoning>Course 15 "Introduction to Machine Learning" covers the foundational concepts
  the student is asking about, including supervised and unsupervised learning. Course 23
  "Deep Learning Fundamentals" would be an excellent follow-up that goes deeper into
  neural networks specifically mentioned in their goal.</reasoning>
</decision>

Example - Generating new course:
<decision>
  <action>GENERATE</action>
  <course_ids></course_ids>
  <reasoning>The student wants to learn about quantum computing applications in
  cryptography, which is a specialized intersection not covered by any existing courses.
  The available computer science courses focus on classical algorithms and the physics
  courses don't cover quantum information theory.</reasoning>
</decision>

Make your decision:
""",
    required_vars=[
        "user_query",
        "courses_xml",
        "course_selection_structure",
    ],
)


def courses_for_selection_to_xml(courses: List[Dict[str, Any]]) -> str:
    """Format a list of courses as XML for course selection prompt.

    Includes id, title, description, and professor name for better matching.

    Args:
        courses: List of course dictionaries with id, title, description,
                and optionally professor_name.

    Returns:
        XML string representation of courses for LLM prompt
    """
    from artificial_u.models.converters import escape_xml

    if not courses:
        return "<no_existing_courses />"

    lines = ["<existing_courses>"]
    for course in courses:
        lines.append("  <course>")
        lines.append(f"    <id>{escape_xml(str(course.get('id', '')))}</id>")
        lines.append(f"    <title>{escape_xml(course.get('title', ''))}</title>")
        lines.append(f"    <description>{escape_xml(course.get('description', ''))}</description>")
        if course.get("professor_name"):
            lines.append(
                f"    <professor>{escape_xml(course.get('professor_name', ''))}</professor>"
            )
        lines.append("  </course>")
    lines.append("</existing_courses>")
    return "\n".join(lines)


def get_course_selection_prompt(
    user_query: str,
    existing_courses: List[Dict[str, Any]],
) -> str:
    """
    Generate a course selection prompt for the quickstart wizard.

    Args:
        user_query: The student's learning goal/query
        existing_courses: List of existing published course dictionaries

    Returns:
        Formatted prompt string for AI course selection
    """
    courses_xml_str = courses_for_selection_to_xml(existing_courses)

    return COURSE_SELECTION_PROMPT.format(
        user_query=user_query,
        courses_xml=courses_xml_str,
        course_selection_structure=COURSE_SELECTION_STRUCTURE,
    )


def _extract_decision_xml(ai_response: str) -> str:
    """Extract decision XML from AI response with fallback for truncated responses.

    Args:
        ai_response: Raw AI response containing <decision> XML

    Returns:
        Extracted decision XML content

    Raises:
        ValueError: If no decision tag can be found
    """
    import logging
    import re

    from artificial_u.models.converters import extract_xml_content

    logger = logging.getLogger(__name__)

    decision_xml = extract_xml_content(ai_response, "decision")

    # Fallback for truncated responses
    if not decision_xml:
        logger.warning("Full <decision> extraction failed, trying fallback for truncated response")
        partial_match = re.search(r"<decision>\s*(.*?)(?:</decision>|$)", ai_response, re.DOTALL)
        if partial_match:
            decision_xml = partial_match.group(1).strip()
        else:
            raise ValueError(f"No <decision> tag found in AI response: {ai_response[:200]}...")

    return decision_xml


def _prepare_xml_for_parsing(decision_xml: str) -> str:
    """Prepare decision XML for parsing, handling truncated reasoning tags.

    Args:
        decision_xml: Raw decision XML content

    Returns:
        Well-formed XML string ready for parsing
    """
    import logging

    logger = logging.getLogger(__name__)

    xml_to_parse = f"<decision>{decision_xml}</decision>"

    # Handle truncated reasoning
    if not decision_xml.strip().endswith(">") and "</reasoning>" not in decision_xml:
        xml_to_parse = f"<decision>{decision_xml}</reasoning></decision>"
        logger.warning("Added missing </reasoning> tag for truncated response")

    return xml_to_parse


def _parse_course_ids(course_ids_text: str) -> List[int]:
    """Parse comma-separated course IDs from text.

    Args:
        course_ids_text: Comma-separated string of course IDs

    Returns:
        List of integer course IDs
    """
    import logging

    logger = logging.getLogger(__name__)

    course_ids = []
    if course_ids_text:
        for id_str in course_ids_text.split(","):
            id_str = id_str.strip()
            if id_str:
                try:
                    course_ids.append(int(id_str))
                except ValueError:
                    logger.warning(f"Skipping non-numeric course ID: {id_str}")

    return course_ids


def _validate_decision(action: str, course_ids: List[int]) -> None:
    """Validate parsed decision data.

    Args:
        action: Decision action ("SELECT" or "GENERATE")
        course_ids: List of course IDs

    Raises:
        ValueError: If validation fails
    """
    if action not in ["SELECT", "GENERATE"]:
        raise ValueError(f"Invalid action in decision: {action}")

    if action == "SELECT" and not course_ids:
        raise ValueError("SELECT action must include at least one course_id")


def parse_course_selection_decision(ai_response: str) -> Dict[str, Any]:
    """
    Parse AI course selection decision response into structured data.

    Args:
        ai_response: Raw AI response containing <decision> XML

    Returns:
        Dictionary containing:
        - action: "SELECT" or "GENERATE"
        - course_ids: List of integer course IDs (empty list if GENERATE)
        - reasoning: String explanation

    Raises:
        ValueError: If the response cannot be parsed
    """
    import xml.etree.ElementTree as ET

    try:
        # Extract and prepare XML
        decision_xml = _extract_decision_xml(ai_response)
        xml_to_parse = _prepare_xml_for_parsing(decision_xml)

        # Parse XML
        root = ET.fromstring(xml_to_parse)

        # Extract components
        action_elem = root.find("action")
        course_ids_elem = root.find("course_ids")
        reasoning_elem = root.find("reasoning")

        action = action_elem.text.strip() if action_elem is not None else None
        reasoning = reasoning_elem.text.strip() if reasoning_elem is not None else None

        # Parse course IDs
        course_ids_text = (
            course_ids_elem.text.strip()
            if course_ids_elem is not None and course_ids_elem.text
            else ""
        )
        course_ids = _parse_course_ids(course_ids_text)

        # Validate
        _validate_decision(action, course_ids)

        return {
            "action": action,
            "course_ids": course_ids,
            "reasoning": reasoning,
        }

    except ET.ParseError as e:
        raise ValueError(f"Failed to parse decision XML: {e}")
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Failed to extract decision data: {e}")
