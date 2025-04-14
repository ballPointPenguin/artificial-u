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
    # Basic professor attributes
    name = professor.name
    gender = professor.gender or "unspecified"
    age = professor.age or "middle-aged"

    # Use description if available, otherwise create a basic description
    if professor.description:
        description = professor.description
    else:
        description = f"A {gender} professor"
        if isinstance(age, int):
            description += f" in their {(age // 10) * 10}s"

    # Format the final prompt with consistent instructions for quality
    prompt = f"""
    A realistic portrait photograph of a university professor named {name}.

    {description}

    Professional attire, soft studio lighting, high-quality, photorealistic,
    detailed facial features, academic setting, neutral background.
    The image should be high-resolution and suitable for a professional academic profile.

    Do not include text or watermarks in the image. Aspect ratio {aspect_ratio}.
    """

    return prompt.strip()
