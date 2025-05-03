"""
Image generation prompts for ArtificialU.
"""


def format_professor_image_prompt(professor, aspect_ratio="1:1") -> str:
    """
    Format a prompt for generating a professor's image.

    Args:
        professor: A Professor object
        aspect_ratio: The aspect ratio for the generated image (default: "1:1")

    Returns:
        A formatted prompt string for the image generation API
    """
    name = professor.name

    # Build description string from available attributes
    description_parts = []

    # Safely get attributes with defaults
    gender = getattr(professor, "gender", None)
    if gender:
        description_parts.append(f"Gender: {gender}")

    age = getattr(professor, "age", None)
    if age:
        description_parts.append(f"Age: {age}")

    description = getattr(professor, "description", None)
    if description:
        description_parts.append(description)

    specialization = getattr(professor, "specialization", None)
    if specialization:
        description_parts.append(f"Specialization: {specialization}")

    description_text = "\n".join(description_parts)

    # Format the final prompt with consistent instructions for quality
    prompt = f"""
A realistic, captivating portrait photograph of a university professor named {name}.

{description_text}

Demeanor is professional yet characterful.
Lighting is soft, possibly with gentle shadows, evoking a thoughtful or
slightly enchanting atmosphere. Background suggests a modern academic setting,
subtly blurred. High-quality, photorealistic, detailed facial features, engaging expression.
The image should be high-resolution and suitable for an intriguing academic profile,
with a slight aura of otherworldliness.

Do not include text or watermarks in the image. Aspect ratio {aspect_ratio}.
    """

    return prompt.strip()
