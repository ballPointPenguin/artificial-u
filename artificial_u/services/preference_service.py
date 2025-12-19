"""
Preference service for ArtificialU.

This service manages application and user preferences.
"""

import logging
from typing import Optional

from artificial_u.config import get_settings
from artificial_u.models.core import Preference
from artificial_u.models.repositories import RepositoryFactory


class PreferenceService:
    """Service for managing application and user preferences."""

    # Preference scope constants
    LECTURE_GENERATION_MODEL = "LECTURE_GENERATION_MODEL"

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize the preference service.

        Args:
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository_factory = repository_factory
        self.settings = get_settings()

    def get_preference(
        self, scope: str, student_id: Optional[int] = None, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a preference value, checking user preference first, then global, then default.

        Args:
            scope: The preference scope/key
            student_id: Optional student ID for user-specific preferences
            default: Default value if no preference is found

        Returns:
            The preference value, or default if not found
        """
        pref = self.repository_factory.preference.get(student_id, scope)
        if pref:
            return pref.value
        return default

    def get_global_preference(self, scope: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a global preference value.

        Args:
            scope: The preference scope/key
            default: Default value if no preference is found

        Returns:
            The preference value, or default if not found
        """
        pref = self.repository_factory.preference.get_global(scope)
        if pref:
            return pref.value
        return default

    def set_global_preference(self, scope: str, value: str) -> Preference:
        """
        Set a global preference.

        Args:
            scope: The preference scope/key
            value: The preference value

        Returns:
            The created or updated Preference object
        """
        return self.repository_factory.preference.set_global(scope, value)

    def set_user_preference(self, student_id: int, scope: str, value: str) -> Preference:
        """
        Set a user-specific preference.

        Args:
            student_id: ID of the student
            scope: The preference scope/key
            value: The preference value

        Returns:
            The created or updated Preference object
        """
        return self.repository_factory.preference.set_user(student_id, scope, value)

    def get_lecture_generation_model(self, student_id: Optional[int] = None) -> str:
        """
        Get the lecture generation model to use.

        Checks in this order:
        1. User-specific preference (if student_id provided)
        2. Global preference
        3. Environment variable / settings default

        Args:
            student_id: Optional student ID for user-specific preferences

        Returns:
            The model name to use for lecture generation
        """
        # Check user preference, then global preference
        model = self.get_preference(
            self.LECTURE_GENERATION_MODEL, student_id=student_id, default=None
        )

        if model:
            self.logger.info(f"Using preference-configured model: {model}")
            return model

        # Fall back to environment variable / settings
        model = self.settings.LECTURE_GENERATION_MODEL
        self.logger.info(f"Using environment-configured model: {model}")
        return model

    def set_lecture_generation_model(self, model: str) -> Preference:
        """
        Set the global lecture generation model preference.

        Args:
            model: The model name (e.g., "claude-opus-4-5")

        Returns:
            The created or updated Preference object
        """
        self.logger.info(f"Setting global lecture generation model to: {model}")
        return self.set_global_preference(self.LECTURE_GENERATION_MODEL, model)
