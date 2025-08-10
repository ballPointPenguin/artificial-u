"""
Utilities for handling XML content from LLM responses.

This module provides functions for detecting truncated responses,
extracting partial XML content, and recovering from incomplete
LLM outputs.
"""

import re
from typing import List, Optional


def detect_truncation(response: str) -> bool:
    """
    Detect if an XML response appears to be truncated.

    Args:
        response: The raw response string from an LLM

    Returns:
        bool: True if the response appears truncated, False otherwise

    Examples:
        >>> detect_truncation("<topic><title>Test</title>")
        True
        >>> detect_truncation("<topic><title>Test</title></topic>")
        False
    """
    # Check for common signs of truncation
    response = response.strip()

    # Look for unclosed tags at the end (but '>' alone is OK if it closes a tag)
    if response.endswith(("<", "</", '="', '"')):
        return True

    # Check if we have opening tags without closing tags
    if "<output>" in response and "</output>" not in response:
        return True

    if "<topics>" in response and "</topics>" not in response:
        return True

    if "<lectures>" in response and "</lectures>" not in response:
        return True

    if "<lecture>" in response and "</lecture>" not in response:
        return True

    # Check if the response ends mid-tag
    if re.search(r"<[^>]*$", response):  # Unclosed tag at end
        return True

    return False


def close_unclosed_tags(xml_fragment: str) -> str:
    """
    Attempt to close unclosed XML tags in a fragment.

    Args:
        xml_fragment: Partial XML that may have unclosed tags

    Returns:
        str: XML fragment with tags closed in reverse order of opening

    Examples:
        >>> close_unclosed_tags("<div><p>Test")
        '<div><p>Test</p></div>'
    """
    # Find all opened tags
    open_tags = []
    for match in re.finditer(r"<([a-zA-Z_][\w\-\.]*)[^>]*>", xml_fragment):
        tag_name = match.group(1)
        # Check if it's not a self-closing tag
        if not match.group(0).endswith("/>"):
            open_tags.append(tag_name)

    # Find all closed tags
    for match in re.finditer(r"</([a-zA-Z_][\w\-\.]*)>", xml_fragment):
        tag_name = match.group(1)
        if tag_name in open_tags:
            open_tags.remove(tag_name)

    # Close remaining unclosed tags in reverse order
    result = xml_fragment
    for tag in reversed(open_tags):
        result += f"</{tag}>"

    return result


def extract_complete_elements(
    xml_content: str, element_name: str, required_children: Optional[List[str]] = None
) -> List[str]:
    """
    Extract all complete XML elements of a given type from potentially truncated content.

    Args:
        xml_content: The XML content to parse (potentially truncated)
        element_name: The name of the XML elements to extract (e.g., "topic", "lecture")
        required_children: Optional list of child elements that must be present

    Returns:
        List[str]: List of complete XML elements as strings
    """
    complete_elements = []

    # First try to find all complete elements
    element_pattern = rf"<{element_name}>.*?</{element_name}>"
    for match in re.finditer(element_pattern, xml_content, re.DOTALL):
        element_text = match.group(0)

        # If required children specified, verify they exist
        if required_children:
            has_all_required = all(
                f"<{child}>" in element_text and f"</{child}>" in element_text
                for child in required_children
            )
            if has_all_required:
                complete_elements.append(element_text)
        else:
            complete_elements.append(element_text)

    return complete_elements


def extract_metadata(xml_content: str, metadata_tags: List[str]) -> dict:
    """
    Extract metadata fields from XML content.

    Args:
        xml_content: The XML content to parse
        metadata_tags: List of metadata tag names to extract

    Returns:
        dict: Dictionary of extracted metadata values
    """
    metadata = {}

    for tag in metadata_tags:
        # Try to extract numeric values
        if any(keyword in tag.lower() for keyword in ["week", "credit", "order", "per"]):
            pattern = rf"<{tag}>(\d+)</{tag}>"
        else:
            pattern = rf"<{tag}>(.*?)</{tag}>"

        match = re.search(pattern, xml_content, re.DOTALL)
        if match:
            metadata[tag] = match.group(1).strip()

    return metadata


def extract_partial_xml_content(
    response: str,
    root_element: str,
    child_element: str,
    required_children: Optional[List[str]] = None,
    metadata_tags: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Try to extract valid XML from a truncated response.

    Args:
        response: The potentially truncated response
        root_element: The root element name (e.g., "topics", "lectures")
        child_element: The child element name (e.g., "topic", "lecture")
        required_children: Optional list of required child elements
        metadata_tags: Optional list of metadata tags to preserve

    Returns:
        Optional[str]: Valid XML if extraction successful, None otherwise
    """
    # Try to find the start of content
    root_match = re.search(rf"<{root_element}>(.*)", response, re.DOTALL)
    if not root_match:
        # Try with output wrapper
        output_match = re.search(rf"<output>\s*<{root_element}>(.*)", response, re.DOTALL)
        if output_match:
            root_match = output_match
        else:
            return None

    partial_content = root_match.group(1)

    # Extract complete child elements
    complete_elements = extract_complete_elements(partial_content, child_element, required_children)

    if not complete_elements and required_children:
        # Try to salvage partial elements that at least have required children
        partial_elements = []

        # Build a pattern that matches elements with all required children
        pattern_parts = [rf"<{child}>(.*?)</{child}>" for child in required_children]
        partial_pattern = rf"<{child_element}>.*?" + ".*?".join(pattern_parts)

        for match in re.finditer(partial_pattern, partial_content, re.DOTALL):
            element_text = match.group(0)
            # Close any unclosed tags
            if f"</{child_element}>" not in element_text:
                element_text = close_unclosed_tags(element_text) + f"</{child_element}>"
            partial_elements.append(element_text)

        complete_elements = partial_elements

    if complete_elements:
        # Extract metadata if requested
        metadata_str = ""
        if metadata_tags:
            metadata = extract_metadata(partial_content, metadata_tags)
            for tag, value in metadata.items():
                metadata_str += f"  <{tag}>{value}</{tag}>\n"

        # Reconstruct valid XML with complete elements only
        xml_output = f"<{root_element}>\n{metadata_str}"
        for element in complete_elements:
            xml_output += f"  {element}\n"
        xml_output += f"</{root_element}>"

        return xml_output

    return None


def ensure_xml_wrapper(content: str, wrapper_tag: str) -> str:
    """
    Ensure that content is wrapped in the specified XML tag.

    Args:
        content: The content to wrap
        wrapper_tag: The tag name to wrap with

    Returns:
        str: Content wrapped in the specified tag
    """
    content = content.strip()

    if not content.startswith(f"<{wrapper_tag}>"):
        content = f"<{wrapper_tag}>\n{content}\n</{wrapper_tag}>"

    return content


def extract_xml_between_tags(text: str, tag_name: str) -> Optional[str]:
    """
    Extract content from between XML tags.

    Args:
        text: Text containing XML tags
        tag_name: The name of the XML tag to extract

    Returns:
        Optional[str]: Extracted content or None if not found
    """
    pattern = rf"<{tag_name}>\s*(.*?)\s*</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)

    return match.group(1).strip() if match else None


def calculate_estimated_tokens(
    items_per_week: int = 3,
    total_weeks: int = 10,
    tokens_per_item: int = 200,
    max_tokens: int = 16384,
) -> int:
    """
    Calculate estimated tokens needed for content generation.

    Args:
        items_per_week: Number of items (topics/lectures) per week
        total_weeks: Total number of weeks
        tokens_per_item: Estimated tokens per item
        max_tokens: Maximum token limit

    Returns:
        int: Estimated tokens needed, capped at max_tokens
    """
    total_items = items_per_week * total_weeks
    estimated_tokens = min(total_items * tokens_per_item, max_tokens)
    return estimated_tokens
