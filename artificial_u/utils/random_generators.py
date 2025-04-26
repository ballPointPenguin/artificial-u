"""
Utility classes for random value generation in ArtificialU.
"""

import random

from artificial_u.config.defaults import DEPARTMENTS


class RandomGenerators:
    """Utility class for generating random values for the university system."""

    @staticmethod
    def generate_department() -> str:
        """Generate a random department name."""
        return random.choice(DEPARTMENTS)

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
