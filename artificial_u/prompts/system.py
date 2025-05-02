"""System prompts shared across generators."""

from typing import Dict

COURSE_SYSTEM_PROMPT = (
    "You are an expert at creating detailed, professional course topics and curricula for a wide range "
    "of academic subjects. "
    "You always respond in valid, indented XML format. "
    "Do not include any explanations, notes, or text outside the XML block."
)

LECTURE_SYSTEM_PROMPT = (
    "You are an expert educational content creator who specializes in developing university-level lectures that "
    "are engaging, informative, and suitable for audio delivery. "
    "You always respond in valid, indented XML format. "
    "Do not include any explanations, notes, or text outside the XML block."
)

GENERIC_XML_SYSTEM_PROMPT = (
    "You always respond in valid, indented XML format. "
    "Do not include any explanations, notes, or text outside the XML block."
)

PROFESSOR_SYSTEM_PROMPT = (
    "You are an expert at creating rich, realistic faculty profiles for an educational content system. "
    "You always respond in valid, indented XML format. "
    "Do not include any explanations, notes, or text outside the XML block."
)

# Dictionary to easily access system prompts by type
SYSTEM_PROMPTS: Dict[str, str] = {
    "professor": PROFESSOR_SYSTEM_PROMPT,
    "course": COURSE_SYSTEM_PROMPT,
    "lecture": LECTURE_SYSTEM_PROMPT,
}


def get_system_prompt(prompt_type: str) -> str:
    """Get a system prompt by type.

    Args:
        prompt_type: The type of system prompt to retrieve

    Returns:
        str: The system prompt

    Raises:
        ValueError: If the prompt type is not found
    """
    if prompt_type not in SYSTEM_PROMPTS:
        raise ValueError(f"Unknown system prompt type: {prompt_type}")

    return SYSTEM_PROMPTS[prompt_type]
