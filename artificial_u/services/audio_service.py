"""
Audio processing service for ArtificialU.
"""

import logging
from typing import Optional, Tuple, Dict, Any, List

from artificial_u.models.core import Lecture, Professor
from artificial_u.utils.exceptions import AudioProcessingError
from artificial_u.services.voice_service import VoiceService
from artificial_u.services.tts_service import TTSService


class AudioService:
    """Service for processing audio in ArtificialU."""

    def __init__(
        self,
        repository,
        api_key: Optional[str] = None,
        audio_path: Optional[str] = None,
        voice_service: Optional[VoiceService] = None,
        tts_service: Optional[TTSService] = None,
        logger=None,
    ):
        """
        Initialize the audio service.

        Args:
            repository: Data repository
            api_key: Optional ElevenLabs API key
            audio_path: Optional path for storing audio files
            voice_service: Optional voice service instance
            tts_service: Optional TTS service instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository = repository

        # Initialize services
        self.voice_service = voice_service or VoiceService(
            api_key=api_key, logger=self.logger
        )
        self.tts_service = tts_service or TTSService(
            api_key=api_key, audio_path=audio_path, logger=self.logger
        )

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
            # Get voice ID for professor if not already assigned
            if (
                not professor.voice_settings
                or "voice_id" not in professor.voice_settings
            ):
                voice_id = self.voice_service.get_voice_id_for_professor(professor)

                # Update professor with voice ID
                if not professor.voice_settings:
                    professor.voice_settings = {}

                professor.voice_settings["voice_id"] = voice_id

                # Update professor in repository
                self.repository.update_professor(professor)
                self.logger.info(
                    f"Updated professor {professor.id} with voice ID {voice_id}"
                )
            else:
                voice_id = professor.voice_settings["voice_id"]

            # Generate audio using TTS service
            audio_path, _ = self.tts_service.generate_lecture_audio(
                lecture=lecture,
                professor=professor,
                voice_id=voice_id,
                save_to_file=True,
            )

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

    def get_voice_for_professor(self, professor: Professor) -> Dict[str, Any]:
        """
        Get voice data for a professor.

        Args:
            professor: The professor object

        Returns:
            Dictionary with voice information
        """
        try:
            return self.voice_service.select_voice_for_professor(professor)
        except Exception as e:
            self.logger.warning(
                f"Failed to get voice for professor {professor.name}: {str(e)}"
            )
            return {}

    def list_available_voices(self, **filters) -> List[Dict[str, Any]]:
        """
        List available voices with optional filtering.

        Args:
            **filters: Filter parameters (gender, accent, age)

        Returns:
            List of voices
        """
        return self.voice_service.list_available_voices(**filters)

    def test_tts_connection(self) -> Dict[str, Any]:
        """
        Test connection to the TTS service.

        Returns:
            Connection status
        """
        return self.tts_service.test_connection()

    def play_audio(self, audio_data_or_path):
        """
        Play audio from data or file path.

        Args:
            audio_data_or_path: Audio data or file path
        """
        self.tts_service.play_audio(audio_data_or_path)
