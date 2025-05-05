"""Department-related prompt templates."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import departments_to_xml, partial_department_to_xml
from artificial_u.prompts.base import PromptTemplate

# XML structure for department profile
DEPARTMENT_XML_STRUCTURE = """<department>
  <name>[Department name]</name>
  <code>[Department code]</code>
  <faculty>[Department faculty]</faculty>
  <description>[Department description]</description>
</department>"""

# Example of a filled department
EXAMPLE_DEPARTMENT_1 = """<department>
  <name>Mathematics</name>
  <code>MTH</code>
  <faculty>Science and Technology</faculty>
  <description>The Department of Mathematics is responsible for teaching and research in
mathematics and its applications.</description>
</department>"""

EXAMPLE_DEPARTMENT_2 = """<department>
  <name>History</name>
  <code>HIS</code>
  <faculty>Arts and Humanities</faculty>
  <description>The Department of History focuses on the study and research of past events
and societies.</description>
</department>"""

# Unified department prompt that handles both structured and freeform inputs
DEPARTMENT_PROMPT = PromptTemplate(
    template=f"""
Generate a department profile in XML format.
Use the structure below; fill in all bracketed placeholders with either provided values
or generated ones if marked as [GENERATE].

XML Structure:
{DEPARTMENT_XML_STRUCTURE}

Existing departments in the university (for context and to avoid repetition):
{{existing_departments_xml}}

Partial Department Details:
{{partial_department_xml}}

{{freeform_prompt_text}}

Examples of properly formatted departments:
Example 1:
{EXAMPLE_DEPARTMENT_1}

Example 2:
{EXAMPLE_DEPARTMENT_2}

IMPORTANT:
- Generate a unique department that doesn't duplicate any existing ones
- Ensure the code is a short, memorable abbreviation (2-8 letters)
- Faculty should be a broad academic division
  (e.g., "Arts and Humanities", "Science and Technology")
- Description should be concise but informative

Wrap your answer in <output> tags, providing only the <department> element.
""",
    required_vars=[
        "existing_departments_xml",
        "partial_department_xml",
    ],
)


def get_department_prompt(
    existing_departments: Optional[List[str]] = None,
    partial_attributes: Optional[Dict[str, Any]] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate a department prompt using centralized converters.

    Args:
        existing_departments: List of existing department names for context
        partial_attributes: Optional dictionary of known attributes to guide generation
        freeform_prompt: Optional freeform text for additional guidance

    Returns:
        Formatted prompt string
    """
    # Use converters to generate XML sections
    existing_departments_xml_str = departments_to_xml(existing_departments or [])
    partial_department_xml_str = partial_department_to_xml(partial_attributes or {})

    # Format freeform prompt if provided
    prompt_text = f"Additional guidance:\n{freeform_prompt}\n" if freeform_prompt else ""

    # Format the main prompt template
    try:
        return DEPARTMENT_PROMPT.format(
            existing_departments_xml=existing_departments_xml_str,
            partial_department_xml=partial_department_xml_str,
            freeform_prompt_text=prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting DEPARTMENT_PROMPT: {e}")
