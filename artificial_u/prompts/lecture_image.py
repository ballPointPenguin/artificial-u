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
    first_slide_url: Optional[str] = None,
    previous_slide_url: Optional[str] = None,
    aspect_ratio: str = "1:1",
) -> Tuple[str, List[str]]:
    """
    Format a highly optimized and structured prompt for generating a lecture slideshow image.
    Follows Gemini native image model best practices (Style, Subject, Setting, Action, Composition).
    """
    professor_name = getattr(professor, "name", "the professor")
    professor_title = getattr(professor, "title", None)
    professor_description = getattr(professor, "description", None)
    professor_specialization = getattr(professor, "specialization", None)
    professor_gender = getattr(professor, "gender", None)
    professor_age = getattr(professor, "age", None)

    # Reference image URLs (multimodal context) - keep order stable.
    refs: List[str] = []
    if professor_image_url:
        refs.append(professor_image_url)
    if first_slide_url:
        refs.append(first_slide_url)
    if previous_slide_url and previous_slide_url != first_slide_url:
        refs.append(previous_slide_url)

    # Truncate texts to prevent prompt bloat and keep generation fast and focused
    def clean_and_truncate(text: Optional[str], max_chars: int) -> str:
        if not text:
            return ""
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    summary_clean = clean_and_truncate(lecture_summary, 300)
    prior_clean = clean_and_truncate(previous_chunk_text, 250)
    current_clean = clean_and_truncate(chunk_text, 600)

    # Build traits string
    traits = []
    if professor_gender:
        traits.append(str(professor_gender))
    if professor_age:
        traits.append(f"Age {professor_age}")
    if professor_title:
        traits.append(str(professor_title))
    traits_str = f" ({', '.join(traits)})" if traits else ""

    # Structure prompt following the Gemini DeepMind guide (Style, Subject, Setting, Action, Composition)
    prompt_parts = [
        (
            "STYLE: Semi-realistic, highly polished digital illustration. "
            "Smooth textures, vivid saturated colors, illustrative digital art style "
            "similar to Riot Games concept art, Hearthstone card art, or ArtStation trending. "
            "NOT photorealistic."
        ),
        f"SUBJECT: Professor {professor_name}{traits_str}. Specialization: {professor_specialization or 'Academic'}. "
        + (f"Appearance details: {professor_description}" if professor_description else ""),
        (
            "SETTING: An idealized academic setting (e.g., a modern lab, "
            "vintage lecture hall, or cozy classroom) that feels warm, inviting, "
            "and slightly magical."
        ),
        f'ACTION/SCENE: Illustrate a key visual element or concept from this moment in the lecture:\n"{current_clean}"'
        + (f'\n\nPrior Context: "{prior_clean}"' if prior_clean else "")
        + (f'\n\nLecture Topic Summary: "{summary_clean}"' if summary_clean else ""),
        (
            "COMPOSITION GUIDANCE:\n"
            "- Maintain strong visual continuity. The professor should look "
            "like the same person as in the reference images (if provided).\n"
            "- Keep it simple and legible: This image will be viewed on small screens "
            "at low resolution (512x512). Do NOT render complex text, dense formulas, "
            "or detailed charts in the background behind the professor. Make background "
            "elements clean and uncluttered.\n"
            "- If showing a visual aid (like a digital slide or whiteboard diagram), "
            "make the visual aid the focal point with large, bold, highly legible graphics.\n"
            "- Ensure correct anatomy: The professor must have exactly two arms and two "
            "hands (no floating hands or extra limbs).\n"
            "- Avoid religious or sacred figure portraits directly; use architecture, "
            "calligraphy, maps, or symbolic imagery for prohibited figures.\n"
            "- Depict historical topics (like slavery or oppression) with gravity and dignity."
        ),
        "LIGHTING & ATMOSPHERE: Volumetric cozy lighting, soft rim lighting, subtle atmospheric glow.",
        f"ASPECT RATIO: {aspect_ratio}",
    ]

    return "\n\n".join(prompt_parts), refs
