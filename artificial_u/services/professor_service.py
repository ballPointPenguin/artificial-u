"""
Professor management service for ArtificialU.
"""

import logging
from typing import Optional

from artificial_u.models.core import Professor
from artificial_u.services.voice_service import VoiceService
from artificial_u.utils.exceptions import DatabaseError, ProfessorNotFoundError
from artificial_u.utils.random_generators import RandomGenerators


class ProfessorService:
    """Service for managing professor entities."""

    def __init__(
        self,
        repository,
        content_generator,
        voice_service=None,
        elevenlabs_api_key=None,
        logger=None,
    ):
        """
        Initialize the professor service.

        Args:
            repository: Data repository
            content_generator: Content generation service
            audio_processor: Deprecated, use voice_service instead
            voice_service: Voice service for voice assignment
            elevenlabs_api_key: API key for ElevenLabs if voice_service not provided
            logger: Optional logger instance
        """
        self.repository = repository
        self.content_generator = content_generator
        self.logger = logger or logging.getLogger(__name__)

        # Set up voice service
        self.voice_service = voice_service
        if not self.voice_service and elevenlabs_api_key:
            self.voice_service = VoiceService(
                api_key=elevenlabs_api_key, logger=self.logger
            )

    def create_professor(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None,
        specialization: Optional[str] = None,
        background: Optional[str] = None,
        teaching_style: Optional[str] = None,
        personality: Optional[str] = None,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        description: Optional[str] = None,
        age: Optional[int] = None,
    ) -> Professor:
        """
        Create a new professor with the given attributes.

        If parameters are not provided, AI generation or defaults will be used.

        Args:
            name: Professor's name
            title: Academic title
            department: Academic department
            specialization: Research specialization
            background: Professional background
            teaching_style: Teaching methodology
            personality: Personality traits
            gender: Professor's gender (optional)
            accent: Professor's accent (optional)
            description: Physical description of the professor (optional)
            age: Professor's age (optional)

        Returns:
            Professor: The created professor object
        """
        self.logger.info("Creating new professor")

        # First, ensure we have department and specialization
        department = department or RandomGenerators.generate_department()
        specialization = specialization or RandomGenerators.generate_specialization(
            department
        )

        # Consolidate provided attributes
        provided_attrs = {
            k: v
            for k, v in {
                "name": name,
                "title": title,
                "background": background,
                "teaching_style": teaching_style,
                "personality": personality,
                "gender": gender,
                "accent": accent,
                "description": description,
                "age": age,
            }.items()
            if v is not None
        }

        # Try AI generation first
        professor = None
        if self.content_generator:
            try:
                professor = self._create_professor_with_ai(
                    department, specialization, provided_attrs
                )
            except Exception as e:
                self.logger.warning(
                    f"AI generation failed, falling back to random generation: {e}"
                )

        # If AI generation failed or wasn't attempted, use random generation
        if professor is None:
            professor = self._create_professor_with_random(
                department, specialization, provided_attrs
            )

        # Assign a voice
        self._assign_voice_to_professor(professor)

        # Save professor to repository
        try:
            saved_professor = self.repository.professor.create(professor)
            self.logger.info(f"Professor created with ID: {saved_professor.id}")
            return saved_professor
        except Exception as e:
            error_msg = f"Failed to save professor: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _create_professor_with_ai(
        self,
        department: str,
        specialization: str,
        provided_attrs: dict,
    ) -> Professor:
        """Helper to create professor using AI content generator."""
        self.logger.info("Using AI to generate professor profile")

        # Determine age range string if we have a specific age
        age_range = None
        age = provided_attrs.get("age")
        if age:
            decade = (age // 10) * 10
            age_range = f"{decade}-{decade+10}"

        # Generate professor using AI
        professor = self.content_generator.create_professor(
            department=department,
            specialization=specialization,
            gender=provided_attrs.get("gender"),
            nationality=None,  # Not currently supported in system interface
            age_range=age_range,
            accent=provided_attrs.get("accent"),
        )

        # Override AI-generated attributes with any provided ones
        for key, value in provided_attrs.items():
            setattr(professor, key, value)

        self.logger.info("Successfully created professor using AI")
        return professor

    def _create_professor_with_random(
        self,
        department: str,
        specialization: str,
        provided_attrs: dict,
    ) -> Professor:
        """Helper to create professor using random generation."""
        self.logger.info("Using random generation for professor profile")

        # Generate or use provided attributes
        attrs = {
            "department": department,
            "specialization": specialization,
            "name": (
                provided_attrs.get("name") or RandomGenerators.generate_professor_name()
            ),
            "title": (
                provided_attrs.get("title")
                or RandomGenerators.generate_professor_title(department)
            ),
            "background": (
                provided_attrs.get("background")
                or RandomGenerators.generate_background(specialization)
            ),
            "teaching_style": (
                provided_attrs.get("teaching_style")
                or RandomGenerators.generate_teaching_style()
            ),
            "personality": (
                provided_attrs.get("personality")
                or RandomGenerators.generate_personality()
            ),
            "gender": (
                provided_attrs.get("gender") or RandomGenerators.generate_gender()
            ),
            "accent": (
                provided_attrs.get("accent") or RandomGenerators.generate_accent()
            ),
            "description": (
                provided_attrs.get("description")
                or RandomGenerators.generate_description(provided_attrs.get("gender"))
            ),
            "age": (provided_attrs.get("age") or RandomGenerators.generate_age()),
        }

        # Log generated/used values
        for key, value in attrs.items():
            self.logger.debug(f"Using {key}: {value}")

        # Create professor object
        return Professor(**attrs)

    def _assign_voice_to_professor(self, professor: Professor) -> None:
        """
        Assign a voice to a professor.

        Args:
            professor: Professor object to assign voice to
        """
        try:
            # If we already have a voice_id, don't override it
            if professor.voice_id:
                self.logger.debug(
                    f"Professor {professor.name} already has voice ID {professor.voice_id}"
                )
                return

            # Use the voice service
            if self.voice_service:
                # Select a voice and update professor record
                voice_data = self.voice_service.select_voice_for_professor(professor)

                # Update local professor object
                if "db_voice_id" in voice_data:
                    professor.voice_id = voice_data["db_voice_id"]
                    self.logger.debug(
                        f"Voice ID {voice_data['db_voice_id']} assigned to professor {professor.name}"
                    )
            else:
                self.logger.warning(
                    f"No voice service available to assign voice to professor {professor.name}"
                )

        except Exception as e:
            error_msg = f"Failed to assign voice to professor: {str(e)}"
            self.logger.warning(error_msg)
            # Not raising an exception here as this is not critical

    def get_professor(self, professor_id: str) -> Professor:
        """
        Get a professor by ID.

        Args:
            professor_id: ID of the professor

        Returns:
            Professor: The professor object

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        professor = self.repository.professor.get(professor_id)
        if not professor:
            error_msg = f"Professor with ID {professor_id} not found"
            self.logger.error(error_msg)
            raise ProfessorNotFoundError(error_msg)
        return professor

    def get_or_create_professor(self, professor_id: Optional[str] = None) -> Professor:
        """
        Get an existing professor by ID or create a new one.

        Args:
            professor_id: ID of the professor to retrieve (optional)

        Returns:
            Professor: The retrieved or created professor

        Raises:
            ProfessorNotFoundError: If professor_id is provided but not found
        """
        if professor_id:
            self.logger.debug(f"Retrieving professor with ID: {professor_id}")
            return self.get_professor(professor_id)
        else:
            self.logger.debug("No professor ID provided, creating new professor")
            return self.create_professor()
