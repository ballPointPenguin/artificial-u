"""Base prompt utilities for Artificial-U."""

from typing import List


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
