"""
Utility classes for random value generation in ArtificialU.
"""

import random
from typing import Dict, List, Optional, Any

from artificial_u.config.defaults import (
    PROFESSOR_TITLES,
    PROFESSOR_LAST_NAMES,
    DEPARTMENTS,
    DEPARTMENT_SPECIALIZATIONS,
    TEACHING_STYLES,
    PERSONALITIES,
    PROFESSOR_GENDERS,
    PROFESSOR_ACCENTS,
    PROFESSOR_AGE_RANGES,
)


class RandomGenerators:
    """Utility class for generating random values for the university system."""

    @staticmethod
    def generate_professor_name() -> str:
        """Generate a random professor name."""
        return f"Dr. {random.choice(PROFESSOR_LAST_NAMES)}"

    @staticmethod
    def generate_department() -> str:
        """Generate a random department name."""
        return random.choice(DEPARTMENTS)

    @staticmethod
    def generate_specialization(department: str) -> str:
        """
        Generate a random specialization based on department.

        Args:
            department: The academic department

        Returns:
            str: A specialization appropriate for the department
        """
        dept_specializations = DEPARTMENT_SPECIALIZATIONS.get(department, ["General"])
        return random.choice(dept_specializations)

    @staticmethod
    def generate_professor_title(department: str) -> str:
        """
        Generate a random academic title for a professor.

        Args:
            department: The academic department

        Returns:
            str: An academic title for the professor
        """
        academic_rank = random.choice(PROFESSOR_TITLES)
        return f"{academic_rank} of {department}"

    @staticmethod
    def generate_background(specialization: str) -> str:
        """
        Generate a background description for a professor.

        Args:
            specialization: The professor's specialization

        Returns:
            str: A background description
        """
        backgrounds = [
            f"Experienced educator with expertise in {specialization}",
            f"Renowned researcher in the field of {specialization}",
            f"Leading expert in {specialization} with extensive teaching experience",
            f"Distinguished scholar specializing in {specialization}",
            f"Pioneering researcher and educator in {specialization}",
        ]
        return random.choice(backgrounds)

    @staticmethod
    def generate_teaching_style() -> str:
        """Generate a random teaching style."""
        return random.choice(TEACHING_STYLES)

    @staticmethod
    def generate_personality() -> str:
        """Generate a random personality trait."""
        return random.choice(PERSONALITIES)

    @staticmethod
    def generate_gender() -> str:
        """Generate a random gender."""
        return random.choice(PROFESSOR_GENDERS)

    @staticmethod
    def generate_accent() -> str:
        """Generate a random accent."""
        return random.choice(PROFESSOR_ACCENTS)

    @staticmethod
    def generate_age() -> int:
        """Generate a random age for a professor."""
        # Professors typically range from 30 to 75
        return random.randint(30, 75)

    @staticmethod
    def generate_description(gender: Optional[str] = None) -> str:
        """
        Generate a basic physical description for a professor.

        Args:
            gender: Optional gender to inform the description

        Returns:
            str: A basic physical description
        """
        # Face shapes
        face_shapes = ["round", "oval", "square", "heart-shaped", "rectangular"]

        # Hair styles and colors
        hair_styles = [
            "short",
            "medium-length",
            "long",
            "curly",
            "straight",
            "wavy",
            "neatly combed",
            "tousled",
            "balding",
        ]
        hair_colors = [
            "black",
            "brown",
            "blonde",
            "red",
            "auburn",
            "salt-and-pepper",
            "gray",
            "white",
            "silver",
        ]

        # Eye colors
        eye_colors = ["brown", "blue", "green", "hazel", "gray"]

        # Clothing styles
        clothing_styles = [
            "formal academic attire",
            "business casual with blazer",
            "professional but approachable style",
            "neat but slightly eccentric style",
            "traditional scholarly look",
            "contemporary professional style",
        ]

        # Accessories
        accessories = [
            "stylish glasses",
            "vintage watch",
            "tasteful jewelry",
            "colorful ties",
            "distinctive scarves",
            "leather briefcase",
            "classic fountain pen",
            "traditional satchel",
        ]

        # Height descriptions
        heights = ["tall", "average height", "short", "statuesque"]

        # Build descriptions
        builds = ["slender", "athletic", "average", "stocky", "slight"]

        # Generate description components
        face_shape = random.choice(face_shapes)
        hair_style = random.choice(hair_styles)
        hair_color = random.choice(hair_colors)
        eye_color = random.choice(eye_colors)
        clothing = random.choice(clothing_styles)
        accessory = random.choice(accessories)
        height = random.choice(heights)
        build = random.choice(builds)

        # Generate basic description
        description = f"A {height}, {build} professor with {hair_style} {hair_color} hair and {eye_color} eyes. "
        description += f"They have a {face_shape} face and typically dress in {clothing}, often seen with {accessory}."

        return description

    @staticmethod
    def generate_lecture_topic(week: int, lecture_number: int) -> str:
        """
        Generate a placeholder lecture topic.

        Args:
            week: The week number
            lecture_number: The lecture number within the week

        Returns:
            str: A placeholder topic
        """
        return f"Topic for Week {week}, Lecture {lecture_number}"
