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
