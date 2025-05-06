"""Course-related prompt templates."""

from typing import Any, Dict, List, Optional

# Import converters instead of defining formatters here
from artificial_u.models.converters import (
    courses_to_xml,
    department_to_xml,
    partial_course_to_xml,
    professor_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

# XML structure for course topics
COURSE_XML_STRUCTURE = """<course>
  <code>[Course code]</code>
  <title>[Course title]</title>
  <description>[Course description]</description>
  <level>[Course level]</level>
  <credits>[Course credits]</credits>
  <lectures_per_week>[Course lectures per week]</lectures_per_week>
  <total_weeks>[Course total weeks]</total_weeks>
</course>"""

# Example courses to demonstrate the format
EXAMPLE_COURSE_1 = """<course>
  <code>CS101</code>
  <title>Introduction to Computer Science</title>
  <description>A beginner-friendly introduction to computer science principles, programming basics,
  and computational thinking.</description>
  <level>Undergraduate</level>
  <credits>3</credits>
  <lectures_per_week>2</lectures_per_week>
  <total_weeks>12</total_weeks>
</course>"""

EXAMPLE_COURSE_2 = """<course>
  <code>HIST220</code>
  <title>Medieval European History</title>
  <description>An exploration of European history from the fall of Rome to the Renaissance,
  examining social, political, and cultural developments.</description>
  <level>Undergraduate</level>
  <credits>4</credits>
  <lectures_per_week>3</lectures_per_week>
  <total_weeks>10</total_weeks>
</course>"""

# Unified course prompt that handles both structured and freeform inputs
COURSE_PROMPT = PromptTemplate(
    template=f"""
Generate the details of an academic course in XML format.
Use the structure below; fill in all bracketed placeholders with either provided values
or generated ones if marked as [GENERATE].

XML Structure:
{COURSE_XML_STRUCTURE}

Existing courses in this department (for context and to avoid repetition):
{{existing_courses_xml}}

Department Information:
{{department_xml}}

Professor Information:
{{professor_xml}}

Partial Course Details:
{{partial_course_xml}}

{{freeform_prompt_text}}

Examples of properly formatted courses:
Example 1:
{EXAMPLE_COURSE_1}

Example 2:
{EXAMPLE_COURSE_2}

Wrap your answer in <output> tags, providing only the <course> element.
""",
    required_vars=[
        "existing_courses_xml",
        "department_xml",
        "professor_xml",
        "partial_course_xml",
        "freeform_prompt_text",
    ],
)


def get_course_prompt(
    existing_courses: List[Dict[str, Any]],
    department_data: Dict[str, Any],
    professor_data: Dict[str, Any],
    partial_course_attrs: Dict[str, Any],
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate a course prompt using centralized converters.

    Args:
        existing_courses: List of existing course attribute dictionaries.
        department_data: Dictionary of department attributes.
        professor_data: Dictionary of professor attributes.
        partial_course_attrs: Dictionary of known/partial course attributes.
        freeform_prompt: Optional freeform text context.

    Returns:
        Formatted prompt string.
    """
    # Use converters to generate XML sections
    existing_courses_xml_str = courses_to_xml(existing_courses)
    department_xml_str = department_to_xml(department_data)
    professor_xml_str = professor_to_xml(professor_data)
    partial_course_xml_str = partial_course_to_xml(partial_course_attrs)

    # Format freeform prompt if provided
    freeform_prompt_text = (
        f"Additional context/ideas for the course:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    # Format the main prompt template
    try:
        return COURSE_PROMPT.format(
            existing_courses_xml=existing_courses_xml_str,
            department_xml=department_xml_str,
            professor_xml=professor_xml_str,
            partial_course_xml=partial_course_xml_str,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        # Re-raise or handle missing required variables if COURSE_PROMPT definition changes
        raise ValueError(f"Error formatting COURSE_PROMPT: {e}")
