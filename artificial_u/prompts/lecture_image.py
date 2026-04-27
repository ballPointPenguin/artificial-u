"""
Image generation prompts for lecture slideshow frames (ArtificialU).
"""

from typing import Any, List, Optional, Tuple


def format_lecture_slide_prompt(  # noqa: C901
    *,
    professor: Any,
    course: Any,
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
    professor_gender = getattr(professor, "gender", None)
    professor_age = getattr(professor, "age", None)
    professor_accent = getattr(professor, "accent", None)

    course_code = getattr(course, "code", None)
    course_title = getattr(course, "title", None)

    # Reference image URLs (multimodal context) - keep order stable.
    refs: List[str] = []
    if professor_image_url:
        refs.append(professor_image_url)
    if previous_slide_url:
        refs.append(previous_slide_url)

    context_lines: List[str] = [
        "Task: Generate an image for the following moment in a lecture.",
        "Professor: "
        + f"{professor_name}"
        + (f" ({professor_title})" if professor_title else "")
        + ".",
    ]

    professor_traits: List[str] = []
    if professor_gender:
        professor_traits.append(str(professor_gender))
    if professor_age:
        professor_traits.append(f"Age {professor_age}")
    if professor_traits:
        context_lines.append(f"Professor traits: {', '.join(professor_traits)}.")
    if professor_accent:
        context_lines.append(f"Professor accent (voice): {professor_accent}.")

    if professor_description:
        context_lines.append(f"Professor description: {professor_description}")
    if professor_specialization:
        context_lines.append(f"Professor specialization: {professor_specialization}")

    course_bits: List[str] = []
    if course_code:
        course_bits.append(str(course_code))
    if course_title:
        course_bits.append(str(course_title))
    if course_bits:
        context_lines.append(f"Course: {' — '.join(course_bits)}")

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
            "Art Direction: Semi-realistic, highly polished digital art. Smooth textures, illustrative style "
            "similar to Riot Games art, Hearthstone card art, or ArtStation trending.",
            "Atmosphere: Subtle atmospheric lighting, a hint of wonder in the air, soft rim lighting.",
            "Background: Idealized academic setting (e.g., a lab or classroom) that feels cozy and slightly "
            "magical.",
            "Details: High resolution, vivid colors, 8k, masterpiece.",
            "",
            "Composition Guidance:",
            "- The professor should feel like the same person as the reference image (if provided).",
            "- If a previous slide reference is provided, preserve visual continuity with it while "
            "adapting to the current lecture moment.",
            "- Mix up the composition. While many frames show the professor, feel free to generate full-screen "
            "visual aids (diagrams, close-ups of objects, slides) when appropriate for the current lecture moment.",
            "- Consider including visual aids relevant to the lecture moment (e.g., a digital slide, "
            "whiteboard, diagrams, instruments, lab apparatus, props).",
            "- Pay close attention to anatomy. Avoid extra limbs on persons or disembodied hands.",
            f"Aspect Ratio: {aspect_ratio}",
        ]
    )

    return "\n".join(context_lines), refs
