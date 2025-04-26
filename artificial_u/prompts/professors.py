"""Professor prompt templates."""

from typing import Any, Dict, List, Optional

from artificial_u.prompts.base import PromptTemplate


def format_existing_professors_xml(existing_professors: List[Dict[str, str]]) -> str:
    """Format a list of existing professors (name, specialization) as XML for prompt context."""
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


# Base template structure for a professor profile
PROFESSOR_XML_STRUCTURE = (
    "<professor>\n"
    "  <name>[Full name with title, e.g., Dr. Jane Doe, Professor John Smith]</name>\n"
    "  <title>[Academic title, e.g., Assistant Professor, Full Professor]</title>\n"
    "  <department_name>[Academic Department, e.g., Computer Science, Philosophy]</department_name>\n"
    "  <specialization>[Area of expertise, e.g., Quantum Computing, Medieval History]</specialization>\n"
    "  <gender>[Professor's gender, e.g., Male, Female, Non-binary]</gender>\n"
    "  <age>[Professor's approximate age as a number, e.g., 45]</age>\n"
    "  <accent>[Professor's accent or speech pattern, e.g., British RP, Mild Southern Drawl, "
    "None noticeable]</accent>\n"
    "  <description>[Detailed physical appearance, clothing style, mannerisms, e.g., Tall, wears tweed jackets, "
    "gestures often]</description>\n"
    "  <background>[Educational and professional history, e.g., PhD from MIT, postdoc at CERN, "
    "worked at Google Research]</background>\n"
    "  <personality>[Key personality traits relevant to teaching, e.g., Enthusiastic, Patient, "
    "Demanding but fair]</personality>\n"
    "  <teaching_style>[Distinctive teaching approach, e.g., Uses Socratic method, Lecture-heavy with multimedia, "
    "Project-based]</teaching_style>\n"
    "</professor>"
)

# Example of a filled profile (concise)
EXAMPLE_PROFESSOR_1 = (
    "<professor>\n"
    "  <name>Dr. Evelyn Reed</name>\n"
    "  <title>Associate Professor</title>\n"
    "  <department_name>Comparative Literature</department_name>\n"
    "  <specialization>20th Century European Fiction</specialization>\n"
    "  <gender>Female</gender>\n"
    "  <age>48</age>\n"
    "  <accent>Standard American</accent>\n"
    "  <description>Sharp dresser, often in dark colors. Intense gaze, speaks precisely. "
    "Short, dark hair.</description>\n"
    "  <background>PhD Yale, Published two monographs.</background>\n"
    "  <personality>Intellectually rigorous, challenges students, appreciates nuanced arguments.</personality>\n"
    "  <teaching_style>Seminar-based discussions, close reading of texts, "
    "high expectations for participation.</teaching_style>\n"
    "</professor>"
)

# Prompt for completing a professor profile with partial info (or generating if minimal info)
PARTIAL_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
Complete the professor profile below.
Use any provided details. For fields marked with [TODO], generate realistic and consistent values.

Existing professors in the university (for context and to avoid repetition):
{{existing_professors_xml}}

Provided details (use these where available, generate for [TODO]):
{{partial_profile_xml}}

Desired complete output format (fill in *all* bracketed placeholders):
{PROFESSOR_XML_STRUCTURE}

Example of a filled profile:
{EXAMPLE_PROFESSOR_1}

Generate the *complete* profile:
<output>
""",
    required_vars=[
        "existing_professors_xml",
        "partial_profile_xml",
    ],
)

# Prompt for generating a completely new professor, inventing everything
OPEN_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
Invent a *new*, creative, or typical university professor.
Generate a detailed profile, including inventing a suitable department name, specialization, and all other details.
Consider the provided list of existing professors to ensure variety and avoid simple repetition.

Existing professors in the university:
{{existing_professors_xml}}

Desired output format (fill in the bracketed placeholders):
{PROFESSOR_XML_STRUCTURE}

Example of a filled profile:
{EXAMPLE_PROFESSOR_1}

Generate the profile for the newly invented professor:
<output>
""",
    required_vars=["existing_professors_xml"],
)


def get_professor_prompt(
    existing_professors: Optional[List[Dict[str, str]]] = None,
    partial_attributes: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Get the appropriate professor generation prompt.
    Uses FULLY_OPEN prompt if no partial attributes are provided,
    otherwise uses PARTIAL prompt to fill in the blanks.

    Args:
        existing_professors: List of existing professors for context.
        partial_attributes: Optional dictionary of known attributes.

    Returns:
        The formatted prompt string ready for the LLM.
    """
    existing_professors = existing_professors or []
    existing_professors_xml = format_existing_professors_xml(existing_professors)
    partial_attributes = partial_attributes or {}

    if not partial_attributes:
        # Case 1: No partial data provided -> Invent everything
        return OPEN_PROFESSOR_PROMPT.format(
            existing_professors_xml=existing_professors_xml
        )
    else:
        # Case 2: Some partial data provided -> Use it and fill in the rest
        partial_profile_xml = format_partial_attributes_xml(partial_attributes)
        return PARTIAL_PROFESSOR_PROMPT.format(
            existing_professors_xml=existing_professors_xml,
            partial_profile_xml=partial_profile_xml,
        )


# Helper function to format partial attributes into XML, marking missing as [TODO]
def format_partial_attributes_xml(partial_attrs: Dict[str, Any]) -> str:
    """Builds the XML string for partial attributes, handling missing fields."""
    lines = ["<professor>"]
    # Define all expected fields in the desired order
    fields = [
        "name",
        "title",
        "department_name",
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
        # Handle provided attributes, including empty strings if deliberately passed
        if value is not None:
            # Ensure age is stringified if it's an int
            lines.append(f"  <{field}>{str(value)}</{field}>")
        else:
            lines.append(f"  <{field}>[TODO]</{field}>")

    lines.append("</professor>")
    return "\n".join(lines)
