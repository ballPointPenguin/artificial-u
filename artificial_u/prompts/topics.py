from typing import Any, Dict, Optional

from artificial_u.models.converters import partial_course_to_xml
from artificial_u.prompts.base import PromptTemplate

TOPICS_XML_STRUCTURE = """<topics>
  <course_title>[Course title]</course_title>
  <lectures_per_week>[Number of topics per week]</lectures_per_week>
  <total_weeks>[Total number of weeks in the course]</total_weeks>
  <topic>
    <title>[Topic title]</title>
    <week>[Week number]</week>
    <order>[Order in week]</order>
  </topic>
  <topic>
    <title>[Topic title]</title>
    <week>[Week number]</week>
    <order>[Order in week]</order>
  </topic>
  <!-- Add more topics as needed -->
</topics>"""

EXAMPLE_TOPICS_1 = """<topics>
  <course_title>Introduction to Computer Science</course_title>
  <lectures_per_week>2</lectures_per_week>
  <total_weeks>12</total_weeks>
  <topic>
    <title>Introduction to Computer Science and Computational Thinking</title>
    <week>1</week>
    <order>1</order>
  </topic>
  <topic>
    <title>History of Computing and Binary Number Systems</title>
    <week>1</week>
    <order>2</order>
  </topic>
  <topic>
    <title>Introduction to Programming: Basic Syntax and Variables</title>
    <week>2</week>
    <order>1</order>
  </topic>
  <topic>
    <title>Control Structures: Conditionals and Loops</title>
    <week>2</week>
    <order>2</order>
  </topic>
  <!-- Additional topics omitted for brevity -->
</topics>"""

EXAMPLE_TOPICS_2 = """<topics>
  <course_title>Medieval European History</course_title>
  <lectures_per_week>3</lectures_per_week>
  <total_weeks>10</total_weeks>
  <topic>
    <title>The Fall of the Roman Empire and the Early Middle Ages</title>
    <week>1</week>
    <order>1</order>
  </topic>
  <topic>
    <title>The Rise of Feudalism and Manorialism</title>
    <week>1</week>
    <order>2</order>
  </topic>
  <topic>
    <title>The Byzantine Empire and Eastern Europe</title>
    <week>1</week>
    <order>3</order>
  </topic>
  <topic>
    <title>The Carolingian Renaissance and Charlemagne's Empire</title>
    <week>2</week>
    <order>1</order>
  </topic>
  <topic>
    <title>Viking Expansion and Its Impact on Europe</title>
    <week>2</week>
    <order>2</order>
  </topic>
  <topic>
    <title>The Development of Early Medieval Christianity</title>
    <week>2</week>
    <order>3</order>
  </topic>
  <!-- Additional topics omitted for brevity -->
</topics>"""

TOPICS_PROMPT = PromptTemplate(
    template=f"""
Generate a list of topics for a course in XML format.
Use the structure below; fill in all bracketed placeholders with either provided values
or generated ones if marked as [GENERATE].

XML Structure:
{TOPICS_XML_STRUCTURE}

Course Information:
{{course_xml}}

{{freeform_prompt_text}}

Examples of properly formatted topics:
Example 1:
{EXAMPLE_TOPICS_1}

Example 2:
{EXAMPLE_TOPICS_2}

Wrap your answer in <output> tags, providing only the <topics> element.
""",
    required_vars=["course_xml", "freeform_prompt_text"],
)


def get_topics_prompt(
    course_data: Dict[str, Any],
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate a list of topics for a course in XML format.

    Args:
      course_data: Dictionary of course attributes.
      freeform_prompt: Optional freeform text context.

    Returns:
      Formatted prompt string.
    """
    course_xml_str = partial_course_to_xml(course_data)

    # Format freeform prompt if provided
    freeform_prompt_text = (
        f"Additional context/ideas for the topics:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    # Format the main prompt template
    try:
        return TOPICS_PROMPT.format(
            course_xml=course_xml_str,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting TOPICS_PROMPT: {e}")
