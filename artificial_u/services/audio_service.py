"""
Audio processing service for ArtificialU.
"""

import logging
from typing import Optional, Tuple

from artificial_u.models.core import Lecture, Professor
from artificial_u.utils.exceptions import AudioProcessingError


class AudioService:
    """Service for processing audio in ArtificialU."""

    def __init__(self, audio_processor, repository, logger=None):
        """
        Initialize the audio service.

        Args:
            audio_processor: Audio processing component
            repository: Data repository
            logger: Optional logger instance
        """
        self.audio_processor = audio_processor
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

    def create_lecture_audio(
        self, course_code: str, week: int, number: int = 1
    ) -> Tuple[str, Lecture]:
        """
        Create audio for a lecture.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week

        Returns:
            Tuple: (audio_path, lecture) - Path to the audio file and the lecture
        """
        self.logger.info(
            f"Creating audio for course {course_code}, week {week}, number {number}"
        )

        # Get course
        course = self.repository.get_course_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Get lecture
        lecture = self.repository.get_lecture_by_course_week_order(
            course_id=course.id, week_number=week, order_in_week=number
        )
        if not lecture:
            error_msg = f"Lecture for course {course_code}, week {week}, number {number} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Get professor
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            error_msg = f"Professor with ID {course.professor_id} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Generate audio
        try:
            audio_path, _ = self.audio_processor.text_to_speech(lecture, professor)
            self.logger.info(f"Audio generated at {audio_path}")
        except Exception as e:
            error_msg = f"Failed to generate audio: {str(e)}"
            self.logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

        # Update lecture with audio path
        try:
            lecture = self.repository.update_lecture_audio(lecture.id, audio_path)
            self.logger.debug(f"Lecture updated with audio path: {audio_path}")
        except Exception as e:
            error_msg = f"Failed to update lecture with audio path: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e

        return audio_path, lecture

    def get_voice_for_professor(self, professor: Professor) -> Optional[str]:
        """
        Get the voice ID for a professor.

        Args:
            professor: The professor object

        Returns:
            Optional[str]: The voice ID if available
        """
        try:
            return self.audio_processor.get_voice_id_for_professor(professor)
        except Exception as e:
            self.logger.warning(
                f"Failed to get voice for professor {professor.name}: {str(e)}"
            )
            return None
