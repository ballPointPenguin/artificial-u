"""Prompt module for Artificial-U.

This module contains template classes and utilities for managing prompts
used across the Artificial-U system.
"""

from artificial_u.prompts.base import PromptTemplate
from artificial_u.prompts.course import get_course_prompt
from artificial_u.prompts.department import get_department_prompt
from artificial_u.prompts.image import format_professor_image_prompt
from artificial_u.prompts.lecture import get_lecture_prompt
from artificial_u.prompts.professor import get_professor_prompt
from artificial_u.prompts.system import get_system_prompt
from artificial_u.prompts.topics import get_topics_prompt

__all__ = [
    # Base utilities
    "PromptTemplate",
    # Course prompts
    "get_course_prompt",
    # Department prompts
    "get_department_prompt",
    # Image prompts
    "format_professor_image_prompt",
    # Lecture prompts
    "get_lecture_prompt",
    # Professor prompts
    "get_professor_prompt",
    # System prompts
    "get_system_prompt",
    # Topics prompts
    "get_topics_prompt",
]
