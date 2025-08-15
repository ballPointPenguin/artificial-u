"""Selection prompt templates for smart course creation."""

from typing import Any, Dict, List

from artificial_u.models.converters import (
    departments_to_xml,
    partial_course_to_xml,
    professors_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

# XML structure for department selection decision
DEPARTMENT_SELECTION_STRUCTURE = """
<decision>
  <action>[SELECT|GENERATE]</action>
  <department_id>[ID or null]</department_id>
  <reasoning>[Detailed explanation]</reasoning>
</decision>
"""

# XML structure for professor selection decision
PROFESSOR_SELECTION_STRUCTURE = """
<decision>
  <action>[SELECT|GENERATE]</action>
  <professor_id>[ID or null]</professor_id>
  <reasoning>[Detailed explanation]</reasoning>
</decision>
"""

# Department selection prompt
DEPARTMENT_SELECTION_PROMPT = PromptTemplate(
    template="""
You are an academic administrator helping to assign courses to appropriate departments.

Given the course details below, analyze the existing departments and decide whether to:
1. SELECT the most appropriate existing department, OR
2. GENERATE a new department if none are suitable

Course Details:
{course_xml}

Existing Departments:
{existing_departments_xml}

Decision Criteria:
- Academic fit: Does the course content align with the department's focus?
- Course level: Is the department appropriate for this course level?
- Existing offerings: Does the department already offer similar courses?

If SELECTING an existing department:
- Choose the best match based on academic alignment
- Use the numeric ID from the departments list above
- Explain your reasoning clearly

If GENERATING a new department:
- Only choose this if no existing department is a reasonable fit
- Explain why none of the existing departments work

Output Format:
{department_selection_structure}

Example - Selecting existing:
<decision>
  <action>SELECT</action>
  <department_id>15</department_id>
  <reasoning>The course "Advanced Machine Learning" is a perfect fit for the Computer Science
  department (ID: 15), which already offers foundational ML courses and has faculty expertise in
  this area.</reasoning>
</decision>

Example - Generating new:
<decision>
  <action>GENERATE</action>
  <department_id>null</department_id>
  <reasoning>This "Sustainable Urban Planning" course combines environmental science, policy,
  and design in a way that doesn't fit cleanly into existing departments. None of the current
  departments (Computer Science, Biology, Economics) have the interdisciplinary focus needed
  for this course.</reasoning>
</decision>

Make your decision:
""",
    required_vars=[
        "course_xml",
        "existing_departments_xml",
        "department_selection_structure",
    ],
)

# Professor selection prompt
PROFESSOR_SELECTION_PROMPT = PromptTemplate(
    template="""
You are an academic administrator helping to assign courses to appropriate professors.

Given the course and department details below, analyze the existing professors and decide
whether to:
1. SELECT the most qualified existing professor, OR
2. GENERATE a new professor if none are suitable

Course Details:
{course_xml}

Department Context:
{department_xml}

Existing Professors in Department:
{existing_professors_xml}

Decision Criteria:
- Subject expertise: Does the professor's specialization align with course content?
- Teaching experience: Has the professor taught similar courses or levels?
- Academic fit: Do the professor's background and style suit this course?

If SELECTING an existing professor:
- Choose the best match based on expertise and teaching fit
- Use the numeric ID from the professors list above
- Explain your reasoning clearly

If GENERATING a new professor:
- Only choose this if no existing professor is reasonably well-suited
- Explain why none of the existing professors are a good match

Output Format:
{professor_selection_structure}

Example - Selecting existing:
<decision>
  <action>SELECT</action>
  <professor_id>42</professor_id>
  <reasoning>Dr. Sarah Chen (ID: 42) specializes in quantum computing and has extensive experience
  teaching graduate-level physics courses. Her background in both theoretical quantum mechanics
  and practical computing applications makes her ideal for "Quantum Information
  Systems".</reasoning>
</decision>

Example - Generating new:
<decision>
  <action>GENERATE</action>
  <professor_id>null</professor_id>
  <reasoning>This "Advanced Forensic Anthropology" course requires very specialized expertise
  in both anthropology and forensic science that none of the existing professors possess.
  The current faculty focus on cultural anthropology and archaeology, but lack the specific
  forensic training needed.</reasoning>
</decision>

Make your decision:
""",
    required_vars=[
        "course_xml",
        "department_xml",
        "existing_professors_xml",
        "professor_selection_structure",
    ],
)


def get_department_selection_prompt(
    course_attributes: Dict[str, Any],
    existing_departments: List[Dict[str, Any]],
) -> str:
    """
    Generate a department selection prompt.

    Args:
        course_attributes: Dictionary of course attributes for context
        existing_departments: List of existing department dictionaries

    Returns:
        Formatted prompt string for AI department selection
    """
    course_xml_str = partial_course_to_xml(course_attributes, generate_marker="[unspecified]")
    existing_departments_xml_str = departments_to_xml(existing_departments)

    return DEPARTMENT_SELECTION_PROMPT.format(
        course_xml=course_xml_str,
        existing_departments_xml=existing_departments_xml_str,
        department_selection_structure=DEPARTMENT_SELECTION_STRUCTURE,
    )


def get_professor_selection_prompt(
    course_attributes: Dict[str, Any],
    department_data: Dict[str, Any],
    existing_professors: List[Dict[str, Any]],
) -> str:
    """
    Generate a professor selection prompt.

    Args:
        course_attributes: Dictionary of course attributes for context
        department_data: Dictionary of department attributes for context
        existing_professors: List of existing professor dictionaries in the department

    Returns:
        Formatted prompt string for AI professor selection
    """
    from artificial_u.models.converters import department_to_xml

    course_xml_str = partial_course_to_xml(course_attributes, generate_marker="[unspecified]")
    department_xml_str = department_to_xml(department_data, missing_marker="[unspecified]")
    existing_professors_xml_str = professors_to_xml(existing_professors)

    return PROFESSOR_SELECTION_PROMPT.format(
        course_xml=course_xml_str,
        department_xml=department_xml_str,
        existing_professors_xml=existing_professors_xml_str,
        professor_selection_structure=PROFESSOR_SELECTION_STRUCTURE,
    )


def _extract_decision_xml(ai_response: str) -> str:
    """Extract decision XML from AI response, handling truncated responses."""
    import logging
    import re

    from artificial_u.models.converters import extract_xml_content

    logger = logging.getLogger(__name__)
    # Try normal extraction first
    decision_xml = extract_xml_content(ai_response, "decision")
    # If full extraction failed, try fallback for truncated responses
    if not decision_xml:
        logger.warning("Full <decision> extraction failed, trying fallback for truncated response")
        # Try to extract partial decision content
        partial_match = re.search(r"<decision>\s*(.*?)(?:</decision>|$)", ai_response, re.DOTALL)
        if partial_match:
            decision_xml = partial_match.group(1).strip()

        else:
            raise ValueError(f"No <decision> tag found in AI response: {ai_response[:200]}...")
    return decision_xml


def _prepare_xml_for_parsing(decision_xml: str) -> str:
    """Prepare decision XML for parsing, handling truncated responses."""
    import logging

    logger = logging.getLogger(__name__)
    xml_to_parse = f"<decision>{decision_xml}</decision>"
    # Handle case where decision_xml might already be truncated but contain incomplete reasoning
    if not decision_xml.strip().endswith(">") and "</reasoning>" not in decision_xml:
        # Response was likely truncated during reasoning - close the reasoning tag
        xml_to_parse = f"<decision>{decision_xml}</reasoning></decision>"
        logger.warning("Added missing </reasoning> tag for truncated response")
    return xml_to_parse


def _parse_entity_id(entity_id, ai_response: str):
    """Parse entity ID from XML element with error handling."""
    if entity_id is None:
        return None
    id_text = entity_id.text.strip()
    if id_text == "null":
        return None
    try:
        return int(id_text)
    except ValueError:
        raise ValueError(
            f"AI returned non-numeric ID '{id_text}' - expected numeric ID "
            f"from the provided list. AI response: {ai_response[:200]}..."
        )


def parse_selection_decision(ai_response: str) -> Dict[str, Any]:
    """
    Parse AI selection decision response into structured data.

    Args:
        ai_response: Raw AI response containing <decision> XML

    Returns:
        Dictionary containing parsed decision data

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

        # Extract decision components
        action = root.find("action")
        dept_element = root.find("department_id")
        prof_element = root.find("professor_id")
        entity_id = dept_element if dept_element is not None else prof_element
        reasoning = root.find("reasoning")

        # Build result
        result = {
            "action": action.text.strip() if action is not None else None,
            "entity_id": _parse_entity_id(entity_id, ai_response),
            "reasoning": reasoning.text.strip() if reasoning is not None else None,
        }

        # Validate that SELECT action has a valid entity_id
        if result["action"] == "SELECT" and result["entity_id"] is None:
            raise ValueError("SELECT action must include valid entity_id")

        return result

    except ET.ParseError as e:
        raise ValueError(f"Failed to parse decision XML: {e}")
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Failed to extract decision data: {e}")
