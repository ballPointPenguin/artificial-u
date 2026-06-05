"""Department-related prompt templates."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    departments_to_xml,
    faculties_to_xml,
    partial_department_to_xml,
)
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
- If a field in 'Partial Department Details' already contains a value (not [GENERATE]),
  copy that value exactly into your output — do not replace or alter it.
- Ensure that both <name> and <code> are unique compared to those listed under
  <existing_departments> (case-insensitive check).
- <code> must be a short, memorable abbreviation (2-8 uppercase letters).
- <faculty> MUST be selected from the <existing_faculties> list below.
  You CANNOT create new faculties - only select from the existing options.
  Choose the most appropriate faculty based on the department's focus.
  Use the exact faculty name as it appears in the list.
- <description> should be clear, concise, and informative about the department's focus.

After generating the profile, validate that <name> and <code> are unique,
that <faculty> exactly matches one from the existing faculties list (case-sensitive),
and that all output fields meet requirements. If validation fails, self-correct and
regenerate the output. Remember: you can only select from existing faculties, never create new ones.
{{existing_departments_xml}}

{{existing_faculties_xml}}

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
        "existing_faculties_xml",
        "partial_department_xml",
    ],
)


def get_department_prompt(
    existing_departments: Optional[List[str]] = None,
    existing_faculties: Optional[List[Dict[str, Any]]] = None,
    partial_attributes: Optional[Dict[str, Any]] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate a department prompt using centralized converters.

    Args:
        existing_departments: List of existing department dicts for context
        existing_faculties: List of existing faculty dicts for selection
        partial_attributes: Optional dictionary of known attributes to guide generation
        freeform_prompt: Optional freeform text for additional guidance

    Returns:
        Formatted prompt string
    """
    # Use converters to generate XML sections
    existing_departments_xml_str = departments_to_xml(existing_departments or [])
    existing_faculties_xml_str = faculties_to_xml(existing_faculties or [])
    partial_department_xml_str = partial_department_to_xml(partial_attributes or {})

    # Format freeform prompt if provided
    prompt_text = f"Additional guidance:\n{freeform_prompt}\n" if freeform_prompt else ""

    # Format the main prompt template
    try:
        return DEPARTMENT_PROMPT.format(
            existing_departments_xml=existing_departments_xml_str,
            existing_faculties_xml=existing_faculties_xml_str,
            partial_department_xml=partial_department_xml_str,
            freeform_prompt_text=prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting DEPARTMENT_PROMPT: {e}")
