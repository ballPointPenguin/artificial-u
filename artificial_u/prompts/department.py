"""Department-related prompt templates."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import departments_to_xml, partial_department_to_xml
from artificial_u.prompts.base import PromptTemplate

# XML structure for department profile
DEPARTMENT_XML_STRUCTURE = """
<output>
  <department>
    <name>[GENERATE]</name>
    <code>[GENERATE]</code>
    <faculty>[GENERATE]</faculty>
    <description>[GENERATE]</description>
  </department>
</output>
"""

# Unified department prompt that handles both structured and freeform inputs
DEPARTMENT_PROMPT = PromptTemplate(
    template=f"""
Generate a new department profile following this XML structure:
{DEPARTMENT_XML_STRUCTURE}

Instructions:
- All fields (inside [GENERATE]) must be filled with generated values.
- Ensure that both <name> and <code> are unique compared to those listed under
  <existing_departments> (case-insensitive check).
- <code> must be a short, memorable abbreviation (2-8 uppercase letters).
- <faculty> should be a broad academic division such as "Arts and Humanities,"
  "Science and Technology," or similar.
- <description> should be clear, concise, and informative about the department's focus.

After generating the profile, validate that <name> and <code> are unique,
and that all output fields meet requirements. If validation fails, self-correct and
regenerate the output.
{{existing_departments_xml}}

Partial Department Details:
{{partial_department_xml}}

{{freeform_prompt_text}}

Formatting and Output Requirements:
- Only output the XML block wrapped in <output> tags,
  containing a single <department> element as shown.
- No external text, notes, or markup outside the <output> block is permitted.
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
