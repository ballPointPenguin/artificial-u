"""Prompt module for Artificial-U.

This module contains template classes and utilities for managing prompts
used across the Artificial-U system.
"""

from artificial_u.prompts.base import PromptTemplate
from artificial_u.prompts.course import get_course_prompt
from artificial_u.prompts.course_image import format_course_image_prompt
from artificial_u.prompts.department import get_department_prompt
from artificial_u.prompts.lecture import get_lecture_prompt
from artificial_u.prompts.professor import get_professor_prompt
from artificial_u.prompts.professor_image import format_professor_image_prompt
from artificial_u.prompts.summary import get_summary_prompt
from artificial_u.prompts.system import get_system_prompt
from artificial_u.prompts.topics import get_next_topic_prompt

__all__ = [
    # Base utilities
    "PromptTemplate",
    # Course prompts
    "get_course_prompt",
    # Department prompts
    "get_department_prompt",
    # Image prompts
    "format_course_image_prompt",
    "format_professor_image_prompt",
    # Lecture prompts
    "get_lecture_prompt",
    # Professor prompts
    "get_professor_prompt",
    # Summary prompts
    "get_summary_prompt",
    # System prompts
    "get_system_prompt",
    # Topics prompts
    "get_next_topic_prompt",
    # Language dispatch
    "get_prompts_for_language",
]

# Registry of supported language codes
SUPPORTED_LANGUAGES = ("en", "fr")


def get_prompts_for_language(language: str = "en"):
    """Return the prompt module for the given language code.

    Callers receive a module with the same public API as this package
    (get_professor_prompt, get_department_prompt, etc.) but with prompts
    written entirely in the target language.

    Args:
        language: ISO 639-1 language code (e.g. "en", "fr"). Defaults to "en".

    Returns:
        Module exposing prompt functions for the requested language.

    Raises:
        ValueError: If the language is not supported.
    """
    if language == "fr":
        from artificial_u.prompts import fr as _fr

        return _fr
    if language == "en":
        import artificial_u.prompts.en as _en

        return _en
    raise ValueError(
        f"Unsupported prompt language: '{language}'. "
        f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
    )
