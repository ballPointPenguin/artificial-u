#!/usr/bin/env python3
"""
Extract content from content_logs JSON files and format as human-friendly markdown.

This script takes a content_logs JSON file and extracts the system_prompt, prompt,
and response, formatting them into a readable markdown file with proper newlines
and XML formatting.
"""

import json
import os
import sys
import xml.dom.minidom
from pathlib import Path


def format_xml_content(xml_string):
    """Format XML content with proper indentation for readability."""
    if not xml_string:
        return xml_string

    try:
        # Try to parse and pretty-print the XML using minidom
        dom = xml.dom.minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Remove the XML declaration line and extra blank lines
        lines = [
            line
            for line in pretty_xml.splitlines()
            if line.strip() and not line.strip().startswith("<?xml")
        ]
        return "\n".join(lines)

    except Exception:
        # If XML parsing fails, fall back to simple formatting
        lines = xml_string.split("\n")
        formatted_lines = []
        indent_level = 0

        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")
                continue

            # Decrease indent for closing tags
            if line.startswith("</"):
                indent_level = max(0, indent_level - 1)

            # Add indentation
            formatted_lines.append("  " * indent_level + line)

            # Increase indent for opening tags (not self-closing)
            if line.startswith("<") and not line.startswith("</") and not line.endswith("/>"):
                indent_level += 1

        return "\n".join(formatted_lines)


def extract_content_from_json(json_file_path, output_file_path=None):
    """
    Extract content from a content_logs JSON file and save as markdown.

    Args:
        json_file_path: Path to the JSON file
        output_file_path: Optional path for output file. If None, uses input filename with .md extension
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{json_file_path}': {e}")
        return False

    # Extract metadata
    metadata = data.get("metadata", {})
    content = data.get("content", {})

    # Generate output filename if not provided
    if output_file_path is None:
        input_path = Path(json_file_path)
        output_file_path = input_path.with_suffix(".md")

    # Create markdown content
    markdown_content = []

    # Header with metadata
    markdown_content.append("# Content Log Analysis")
    markdown_content.append("")
    markdown_content.append(f"**Timestamp:** {metadata.get('timestamp', 'Unknown')}")
    markdown_content.append(f"**Backend:** {metadata.get('backend', 'Unknown')}")
    markdown_content.append(f"**Model:** {metadata.get('model', 'Unknown')}")

    settings = metadata.get("settings", {})
    if settings:
        markdown_content.append("**Settings:**")
        for key, value in settings.items():
            markdown_content.append(f"- {key}: {value}")

    markdown_content.append("")
    markdown_content.append("---")
    markdown_content.append("")

    # System Prompt
    system_prompt = content.get("system_prompt")
    if system_prompt:
        markdown_content.append("## System Prompt")
        markdown_content.append("")
        markdown_content.append(system_prompt)
        markdown_content.append("")

    # Main Prompt
    prompt = content.get("prompt")
    if prompt:
        markdown_content.append("## Prompt")
        markdown_content.append("")
        markdown_content.append(prompt)
        markdown_content.append("")

    # Prefill (if present)
    prefill = content.get("prefill")
    if prefill:
        markdown_content.append("## Prefill")
        markdown_content.append("")
        markdown_content.append(prefill)
        markdown_content.append("")

    # Response
    response = content.get("response")
    if response:
        markdown_content.append("## Response")
        markdown_content.append("")

        # Check if response looks like XML
        if response.strip().startswith("<"):
            markdown_content.append("```xml")
            markdown_content.append(format_xml_content(response))
            markdown_content.append("```")
        else:
            # Regular text response
            markdown_content.append(response)

        markdown_content.append("")

    # Write to file
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(markdown_content))
        print(f"Content extracted to: {output_file_path}")
        return True
    except Exception as e:
        print(f"Error writing to file '{output_file_path}': {e}")
        return False


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python extract_content.py <json_file> [output_file]")
        print("")
        print("Examples:")
        print(
            "  python extract_content.py content_logs/20251021_054846_040463_anthropic_claude-sonnet-4-5-20250929.json"
        )
        print(
            "  python extract_content.py content_logs "
            " 20251021_054846_040463_anthropic_claude-sonnet-4-5-20250929.json output.md"
        )
        sys.exit(1)

    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Check if input file exists
    if not os.path.exists(json_file):
        print(f"Error: Input file '{json_file}' does not exist.")
        sys.exit(1)

    success = extract_content_from_json(json_file, output_file)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
