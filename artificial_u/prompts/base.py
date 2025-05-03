"""Base prompt utilities for Artificial-U."""

import re
from typing import List, Optional


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


# XML Utilities
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
