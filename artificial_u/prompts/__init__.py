"""Prompt module for Artificial-U.

This module contains template classes and utilities for managing prompts
used across the Artificial-U system.
"""

from artificial_u.prompts.base import (
    PromptTemplate,
    StructuredPrompt,
    xml_tag,
    extract_xml_content,
    extract_xml_sections,
)
