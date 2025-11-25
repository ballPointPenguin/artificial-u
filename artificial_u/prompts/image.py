"""
Image generation prompts for ArtificialU.
"""


def format_professor_image_prompt(professor, aspect_ratio: str = "1:1") -> str:
    """
    Format a prompt for generating a professor's image.

    Args:
        professor: A Professor object
        aspect_ratio: The aspect ratio for the generated image (default: "1:1")

    Returns:
        A formatted prompt string for the image generation API
    """
    name = professor.name
    gender = getattr(professor, "gender", None)
    age = getattr(professor, "age", None)
    description = getattr(professor, "description", None)
    specialization = getattr(professor, "specialization", None)

    # Build subject line
    subject_parts = [f"Subject: A university professor named {name}."]
    if gender:
        subject_parts.append(f"{gender},")
    if age:
        subject_parts.append(f"Age {age}.")
    subject_line = " ".join(subject_parts)

    # Build appearance section
    appearance_line = ""
    if description:
        appearance_line = f"Appearance: {description}"

    # Build specialization section
    specialization_line = ""
    if specialization:
        specialization_line = f"Specialization: {specialization}."

    # Format the structured prompt
    prompt_sections = [subject_line]

    if appearance_line:
        prompt_sections.append(appearance_line)

    if specialization_line:
        prompt_sections.append(specialization_line)

    prompt_sections.extend(
        [
            "",
            "Art Direction: A semi-realistic, highly polished digital art portrait. "
            "Smooth textures, illustrative style similar to Riot Games art, "
            "Hearthstone card art, or ArtStation trending.",
            "Negative Prompt: Do not make this photorealistic. Do not make it grainy.",
            "Atmosphere: Subtle atmospheric lighting, a hint of wonder in the air, "
            "soft rim lighting, very faint floating dust motes.",
            "Background: A blurred, idealized academic setting (lab or library) "
            "that feels cozy and slightly magical.",
            'Lighting: Volumetric, cinematic, perfectly lit with no harsh shadows, "hero" lighting.',
            "Details: High resolution, vivid colors, 8k, masterpiece.",
            f"Aspect Ratio: {aspect_ratio}",
        ]
    )

    return "\n".join(prompt_sections)
