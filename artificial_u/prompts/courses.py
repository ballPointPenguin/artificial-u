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
  <topics>
    <week number="[Week number]">
      <lecture number="1">
        <topic>[Topic for first lecture of the week]</topic>
      </lecture>
      <lecture number="2">
        <topic>[Topic for second lecture of the week, if lectures_per_week > 1]</topic>
      </lecture>
      <!-- Add more lectures as needed based on lectures_per_week -->
    </week>
    <!-- Repeat for each week up to total_weeks -->
  </topics>
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
  <topics>
    <week number="1">
      <lecture number="1">
        <topic>Introduction to Computer Science and Computational Thinking</topic>
      </lecture>
      <lecture number="2">
        <topic>History of Computing and Binary Number Systems</topic>
      </lecture>
    </week>
    <week number="2">
      <lecture number="1">
        <topic>Introduction to Programming: Basic Syntax and Variables</topic>
      </lecture>
      <lecture number="2">
        <topic>Control Structures: Conditionals and Loops</topic>
      </lecture>
    </week>
    <!-- Additional weeks omitted for brevity -->
  </topics>
</course>"""

EXAMPLE_COURSE_2 = """<course>
  <code>HIST220</code>
  <title>Medieval European History</title>
  <description>An exploration of European history from the fall of Rome to the Renaissance, examining
  social, political, and cultural developments.</description>
  <level>Undergraduate</level>
  <credits>4</credits>
  <lectures_per_week>3</lectures_per_week>
  <total_weeks>10</total_weeks>
  <topics>
    <week number="1">
      <lecture number="1">
        <topic>The Fall of the Roman Empire and the Early Middle Ages</topic>
      </lecture>
      <lecture number="2">
        <topic>The Rise of Feudalism and Manorialism</topic>
      </lecture>
      <lecture number="3">
        <topic>The Byzantine Empire and Eastern Europe</topic>
      </lecture>
    </week>
    <week number="2">
      <lecture number="1">
        <topic>The Carolingian Renaissance and Charlemagne's Empire</topic>
      </lecture>
      <lecture number="2">
        <topic>Viking Expansion and Its Impact on Europe</topic>
      </lecture>
      <lecture number="3">
        <topic>The Development of Early Medieval Christianity</topic>
      </lecture>
    </week>
    <!-- Additional weeks omitted for brevity -->
  </topics>
</course>"""

# Unified course prompt that handles both structured and freeform inputs
COURSE_PROMPT = PromptTemplate(
    template=f"""
Generate a course with a nested sequence of lecture topics in XML format.
Use the structure below; fill in all bracketed placeholders with either provided values or generated ones if marked as [GENERATE].

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

IMPORTANT: Make sure that the number of lectures per week in your response matches the specified lectures_per_week value.
For each week, generate exactly the number of lectures specified in lectures_per_week.

Wrap your answer in <output> tags, providing only the <course> element:
<output>
""",
    required_vars=[
        "existing_courses_xml",
        "partial_course_xml",
        "professor_xml",
        "department_xml",
    ],
)


def get_course_prompt(
    department_data: Dict[str, Any],
    professor_data: Dict[str, Any],
    existing_courses: List[Dict[str, Any]],
    partial_course_attrs: Dict[str, Any],
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate a course topics prompt using centralized converters.

    Args:
        department_data: Dictionary of department attributes.
        professor_data: Dictionary of professor attributes.
        existing_courses: List of existing course attribute dictionaries.
        partial_course_attrs: Dictionary of known/partial course attributes.
        freeform_prompt: Optional freeform text context.

    Returns:
        Formatted prompt string.
    """
    # Use converters to generate XML sections
    department_xml_str = department_to_xml(department_data)
    professor_xml_str = professor_to_xml(professor_data)
    # courses_to_xml expects list of dicts, which is what course_service provides
    existing_courses_xml_str = courses_to_xml(existing_courses)
    # partial_course_to_xml expects dict of partial attributes
    partial_course_xml_str = partial_course_to_xml(partial_course_attrs)

    # Format freeform prompt if provided
    freeform_prompt_text = (
        f"Additional context/ideas for the course:\n{freeform_prompt}\n"
        if freeform_prompt
        else ""
    )

    # Format the main prompt template
    try:
        return COURSE_PROMPT.format(
            existing_courses_xml=existing_courses_xml_str,
            partial_course_xml=partial_course_xml_str,
            professor_xml=professor_xml_str,
            department_xml=department_xml_str,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        # Re-raise or handle missing required variables if COURSE_PROMPT definition changes
        raise ValueError(f"Error formatting COURSE_PROMPT: {e}")
