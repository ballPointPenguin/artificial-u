"""Prompt module for Artificial-U.

This module contains template classes and utilities for managing prompts
used across the Artificial-U system.
"""

from artificial_u.prompts.base import (
    PromptTemplate,
    extract_xml_content,
)
from artificial_u.prompts.courses import get_course_prompt
from artificial_u.prompts.department import (
    get_department_prompt,
    get_open_department_prompt,
)
from artificial_u.prompts.images import format_professor_image_prompt
from artificial_u.prompts.lectures import get_lecture_prompt
from artificial_u.prompts.professors import get_professor_prompt
from artificial_u.prompts.system import get_system_prompt

__all__ = [
    # Base utilities
    "PromptTemplate",
    "extract_xml_content",
    # Course prompts
    "get_course_prompt",
    # Department prompts
    "get_department_prompt",
    "get_open_department_prompt",
    # Image prompts
    "format_professor_image_prompt",
    # Lecture prompts
    "get_lecture_prompt",
    # Professor prompts
    "get_professor_prompt",
    # System prompts
    "get_system_prompt",
]
