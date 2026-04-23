"""
Image generation prompts for lecture slideshow frames (ArtificialU).
"""

from typing import Any, List, Optional, Tuple


def format_lecture_slide_prompt(  # noqa: C901
    *,
    professor: Any,
    course: Any,
    topic: Any,
    lecture_summary: Optional[str],
    chunk_text: str,
    previous_chunk_text: Optional[str] = None,
    professor_image_url: Optional[str] = None,
    previous_slide_url: Optional[str] = None,
    aspect_ratio: str = "1:1",
) -> Tuple[str, List[str]]:
    """
    Format a prompt for generating a lecture slideshow image.

    Returns:
        (prompt_text, reference_image_urls)
    """
    professor_name = getattr(professor, "name", "the professor")
    professor_title = getattr(professor, "title", None)
    professor_description = getattr(professor, "description", None)
    professor_specialization = getattr(professor, "specialization", None)

    course_code = getattr(course, "code", None)
    course_title = getattr(course, "title", None)

    topic_title = getattr(topic, "title", None)
    topic_week = getattr(topic, "week", None)
    topic_order = getattr(topic, "order", None)

    # Reference image URLs (multimodal context) - keep order stable.
    refs: List[str] = []
    if professor_image_url:
        refs.append(professor_image_url)
    if previous_slide_url:
        refs.append(previous_slide_url)

    context_lines: List[str] = [
        "Task: Generate a lecture slide image for the following moment in a lecture.",
        "Professor: "
        + f"{professor_name}"
        + (f" ({professor_title})" if professor_title else "")
        + ".",
    ]

    if professor_description:
        context_lines.append(f"Professor appearance: {professor_description}")
    if professor_specialization:
        context_lines.append(f"Professor specialization: {professor_specialization}")

    course_bits: List[str] = []
    if course_code:
        course_bits.append(str(course_code))
    if course_title:
        course_bits.append(str(course_title))
    if course_bits:
        context_lines.append(f"Course: {' — '.join(course_bits)}")

    topic_bits: List[str] = []
    if topic_week is not None:
        topic_bits.append(f"Week {topic_week}")
    if topic_order is not None:
        topic_bits.append(f"Lecture {topic_order}")
    if topic_title:
        topic_bits.append(str(topic_title))
    if topic_bits:
        context_lines.append(f"Topic: {' — '.join(topic_bits)}")

    if lecture_summary:
        context_lines.append("")
        context_lines.append("Lecture summary (optional context):")
        context_lines.append(lecture_summary.strip())

    if previous_chunk_text:
        context_lines.append("")
        context_lines.append("Immediately prior context (optional):")
        context_lines.append(previous_chunk_text.strip())

    context_lines.append("")
    context_lines.append("Current lecture moment (primary source text):")
    context_lines.append(chunk_text.strip())

    context_lines.extend(
        [
            "",
            "Art Direction:",
            "- The professor should feel like the same person as the reference image (if provided).",
            "- Prefer educational, textbook-like visuals where appropriate "
            "(diagrams, labeled illustrations, maps, charts).",
            "- Compose like a lecture slide or visual aid that supports what is being said here.",
            "- Avoid watermarks, UI chrome, screenshots of apps, and random unrelated logos.",
            f"Aspect Ratio: {aspect_ratio}",
        ]
    )

    return "\n".join(context_lines), refs
