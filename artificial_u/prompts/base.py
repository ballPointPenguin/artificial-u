"""Base prompt utilities for Artificial-U."""

import os
import re
from typing import Any, Dict, List, Optional, Union

import anthropic


class PromptTemplate:
    """Base class for prompt templates."""

    def __init__(self, template: str, required_vars: List[str] = None):
        """Initialize a prompt template.

        Args:
            template: The prompt template string with {variable} placeholders
            required_vars: Required variables that must be provided
        """
        self.template = template
        self.required_vars = required_vars or []

    def format(self, **kwargs) -> str:
        """Format the template with the provided variables."""
        # Check required variables
        missing = [var for var in self.required_vars if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        # Format the template
        return self.template.format(**kwargs)

    def __call__(self, **kwargs) -> str:
        """Allow calling the template as a function."""
        return self.format(**kwargs)


class StructuredPrompt:
    """A structured prompt with sections that can be enabled/disabled."""

    def __init__(self):
        """Initialize a structured prompt."""
        self.sections = {}
        self.order = []

    def add_section(
        self,
        name: str,
        content: str,
        enabled: bool = True,
        position: Optional[int] = None,
    ):
        """Add a section to the prompt.

        Args:
            name: Section name
            content: Section content
            enabled: Whether the section is enabled
            position: Optional position in the order (default: append)
        """
        self.sections[name] = {"content": content, "enabled": enabled}

        if position is not None:
            self.order.insert(position, name)
        else:
            self.order.append(name)

    def enable_section(self, name: str):
        """Enable a section."""
        if name in self.sections:
            self.sections[name]["enabled"] = True

    def disable_section(self, name: str):
        """Disable a section."""
        if name in self.sections:
            self.sections[name]["enabled"] = False

    def render(self) -> str:
        """Render the complete prompt."""
        result = []
        for name in self.order:
            section = self.sections.get(name)
            if section and section["enabled"]:
                result.append(section["content"])

        return "\n\n".join(result)


# XML Tag Utilities
def xml_tag(tag_name: str, content: str) -> str:
    """Wrap content in XML tags.

    Args:
        tag_name: The name of the XML tag
        content: The content to wrap

    Returns:
        str: Content wrapped in XML tags
    """
    return f"<{tag_name}>\n{content}\n</{tag_name}>"


def extract_xml_content(text: str, tag_name: str) -> Optional[str]:
    """Extract content from XML tags.

    Args:
        text: Text containing XML tags
        tag_name: The name of the XML tag to extract

    Returns:
        Optional[str]: Extracted content or None if not found
    """
    pattern = rf"<{tag_name}>\s*(.*?)\s*</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)

    return match.group(1).strip() if match else None


def extract_xml_sections(text: str) -> Dict[str, str]:
    """Extract all XML sections from text.

    Args:
        text: Text containing XML tags

    Returns:
        Dict[str, str]: Dictionary of tag names to contents
    """
    # Find all XML tags in the text
    pattern = r"<([a-zA-Z0-9_]+)>\s*(.*?)\s*</\1>"
    matches = re.finditer(pattern, text, re.DOTALL)

    result = {}
    for match in matches:
        tag_name = match.group(1)
        content = match.group(2).strip()
        result[tag_name] = content

    return result
