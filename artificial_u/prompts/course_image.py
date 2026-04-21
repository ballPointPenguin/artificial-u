"""
Image generation prompts for course album art (ArtificialU).
"""

from typing import Any, Optional


def _truncate_for_themes(text: str, max_len: int = 500) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def format_course_image_prompt(
    course: Any,
    professor: Optional[Any] = None,
    aspect_ratio: str = "1:1",
) -> str:
    """
    Format a prompt for generating square album-art style course imagery.

    Args:
        course: A Course object (title, code, level, description expected).
        professor: Optional Professor object; name may appear in optional credits.
        aspect_ratio: The aspect ratio for the generated image (default: "1:1").

    Returns:
        A formatted prompt string for the image generation API.
    """
    title = getattr(course, "title", None) or "Untitled course"
    code = getattr(course, "code", None)
    level = getattr(course, "level", None)
    description = getattr(course, "description", None)

    course_parts = [f"Course: {title}"]
    if code:
        course_parts.append(f"Code: {code}.")
    if level:
        course_parts.append(f"Level: {level}.")
    course_line = " ".join(course_parts)

    themes_line = ""
    if description:
        themes_line = (
            "Themes (inform visuals only; do not render as a paragraph of text): "
            f"{_truncate_for_themes(description)}"
        )

    prof_name = getattr(professor, "name", None) if professor is not None else None
    optional_credits = ""
    if prof_name:
        optional_credits = (
            f"Optional credits: You may include the instructor name ({prof_name}) "
            "in lettering if it fits the 0–12 word limit; it is not required."
        )

    prompt_sections = [
        "Subject: Album art for a university course.",
        course_line,
    ]

    if themes_line:
        prompt_sections.append(themes_line)

    if optional_credits:
        prompt_sections.append(optional_credits)

    prompt_sections.extend(
        [
            "",
            "Art Direction: Highly polished digital illustration in the spirit of album cover art "
            "(think eclectic SoHo record store, a weird aunt's basement crate, "
            "or a festival merch stand). Semi-realistic, smooth textures, illustrative style "
            "similar to Riot Games art, Hearthstone key art, or ArtStation trending — "
            "but as a record sleeve / square thumbnail, not a portrait.",
            "Vibe: Maximalism encouraged. Pursue diverse, unique moods; saturated or moody palettes; "
            "motif and color should read clearly at thumbnail size. Do NOT converge on one "
            "house style — vary composition, palette, era nods, and graphic idiom between runs.",
            "Typography: Use between 0 and 12 words of text total on the image. "
            "Course title is encouraged but may be abbreviated if long. "
            "Do not add any product branding, URLs, or the string 'Artificial-U'. "
            "Keep lettering legible; no paragraphs or walls of text.",
            "Negative Prompt: Not photorealistic. Not grainy. Not a portrait of a person. "
            "No watermarks. No lorem ipsum. No academic-stock clichés (chalkboards, graduation "
            "caps) unless the course title clearly demands them.",
            "Details: High resolution, vivid colors, 8k, masterpiece.",
            f"Aspect Ratio: {aspect_ratio}",
        ]
    )

    return "\n".join(prompt_sections)
