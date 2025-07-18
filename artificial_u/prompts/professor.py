"""Professor prompt templates."""

from typing import Any, Dict, List, Optional

# Import converters
from artificial_u.models.converters import partial_professor_to_xml, professors_to_xml
from artificial_u.prompts.base import PromptTemplate

# Base template structure for a professor profile
PROFESSOR_XML_STRUCTURE = (
    "<professor>\n"
    "  <name>[GENERATE]</name>\n"
    "  <title>[GENERATE]</title>\n"
    "  <department_name>[GENERATE]</department_name>\n"
    "  <specialization>[GENERATE]</specialization>\n"
    "  <gender>[GENERATE]</gender>\n"
    "  <age>[GENERATE]</age>\n"
    "  <accent>[GENERATE]</accent>\n"
    "  <description>[GENERATE]</description>\n"
    "  <background>[GENERATE]</background>\n"
    "  <personality>[GENERATE]</personality>\n"
    "  <teaching_style>[GENERATE]</teaching_style>\n"
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
    "  <personality>Intellectually rigorous, challenges students, appreciates nuanced arguments."
    "  </personality>\n"
    "  <teaching_style>Seminar-based discussions, close reading of texts, "
    "high expectations for participation.</teaching_style>\n"
    "</professor>"
)

# Prompt for completing a professor profile with partial info (or generating if minimal info)
PARTIAL_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
{{freeform_prompt_text}}
Complete the professor profile below.
Use any provided details. For fields marked with [GENERATE], generate realistic and "
    "consistent values.

Existing professors in the university (for context and to avoid repetition):
{{existing_professors_xml}}

Provided details (use these where available, generate for [GENERATE]):
{{partial_profile_xml}}

Desired complete output format (fill in *all* bracketed placeholders):
{PROFESSOR_XML_STRUCTURE}

Example of a filled profile:
{EXAMPLE_PROFESSOR_1}

Generate the *complete* profile.
Wrap your answer in <output> tags, providing only the <professor> element.
""",
    required_vars=[
        "existing_professors_xml",
        "partial_profile_xml",
    ],
)

# Prompt for generating a completely new professor, inventing everything
OPEN_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
{{freeform_prompt_text}}
Generate a detailed professor profile based on the above context and inspiration.
Create a complete, realistic academic profile including department, specialization, and all personal
details. Consider the provided list of existing professors to ensure variety and avoid simple
repetition.

Existing professors in the same department:
{{existing_professors_xml}}

Desired output format (fill in all bracketed placeholders):
{PROFESSOR_XML_STRUCTURE}

Example of a filled profile:
{EXAMPLE_PROFESSOR_1}

Generate the complete professor profile.
Wrap your answer in <output> tags, providing only the <professor> element.
""",
    required_vars=["existing_professors_xml"],
)

# New prompt specifically for guided professor generation
GUIDED_PROFESSOR_PROMPT = PromptTemplate(
    template=f"""
{{freeform_prompt_text}}

Using the above description as inspiration and guidance, create a professor profile that captures
the essence, style, and characteristics described. You should create a professor who embodies the
qualities, background, and teaching approach outlined above.
Consider the provided list of existing professors to ensure variety and avoid simple repetition.

Existing professors in the same department:
{{existing_professors_xml}}

Desired output format (fill in all bracketed placeholders):
{PROFESSOR_XML_STRUCTURE}

Example of a filled profile:
{EXAMPLE_PROFESSOR_1}

Generate the professor profile that matches the provided description.
Wrap your answer in <output> tags, providing only the <professor> element.
""",
    required_vars=["existing_professors_xml"],
)


def get_professor_prompt(
    existing_professors: Optional[List[Dict[str, str]]] = None,
    partial_attributes: Optional[Dict[str, Any]] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """
    Get the appropriate professor generation prompt using converters.
    Uses different prompt templates based on the input provided.

    Args:
        existing_professors: List of existing professors (dicts with name/specialization) for
            context.
        partial_attributes: Optional dictionary of known attributes.
        freeform_prompt: Optional freeform text for additional guidance.

    Returns:
        The formatted prompt string ready for the LLM.
    """
    existing_professors = existing_professors or []
    # Use converter for existing professors
    existing_professors_xml_str = professors_to_xml(existing_professors)
    partial_attributes = partial_attributes or {}

    if freeform_prompt:
        # When freeform prompt is provided, determine the appropriate framing
        if not partial_attributes:
            # Case 1: Freeform prompt with no partial data -> Use as inspiration/guidance
            prompt_text = f"INSPIRATION AND CONTEXT:\n{freeform_prompt}\n\n"
            return GUIDED_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                freeform_prompt_text=prompt_text,
            )
        else:
            # Case 2: Freeform prompt with partial data -> Use as context for completion
            prompt_text = (
                f"CONTEXT AND GUIDANCE:\n{freeform_prompt}\n\n"
                f"Use the above context to guide your completion of the profile below.\n\n"
            )
            partial_profile_xml_str = partial_professor_to_xml(partial_attributes)
            return PARTIAL_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                partial_profile_xml=partial_profile_xml_str,
                freeform_prompt_text=prompt_text,
            )
    else:
        # No freeform prompt provided
        if not partial_attributes:
            # Case 3: No freeform prompt, no partial data -> General generation
            prompt_text = (
                "Create a realistic, detailed professor profile with invented characteristics.\n\n"
            )
            return OPEN_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                freeform_prompt_text=prompt_text,
            )
        else:
            # Case 4: No freeform prompt, but partial data -> Simple completion
            prompt_text = ""
            partial_profile_xml_str = partial_professor_to_xml(partial_attributes)
            return PARTIAL_PROFESSOR_PROMPT.format(
                existing_professors_xml=existing_professors_xml_str,
                partial_profile_xml=partial_profile_xml_str,
                freeform_prompt_text=prompt_text,
            )
