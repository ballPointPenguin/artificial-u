"""
Audio processing service for ArtificialU.
"""

import logging
import os
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.models.core import Lecture
from artificial_u.services.storage_service import StorageService
from artificial_u.services.tts_service import TTSService
from artificial_u.utils.exceptions import AudioProcessingError


class AudioService:
    """Service for processing audio in ArtificialU."""

    def __init__(
        self,
        repository,
        api_key: Optional[str] = None,
        tts_service: Optional[TTSService] = None,
        storage_service: Optional[StorageService] = None,
        logger=None,
    ):
        """
        Initialize the audio service.

        Args:
            repository: Data repository
            api_key: Optional ElevenLabs API key
            tts_service: Optional TTS service instance
            storage_service: Optional storage service instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository = repository

        # Initialize services
        storage_settings = (storage_service or StorageService()).settings
        temp_audio_path = storage_settings.TEMP_AUDIO_PATH

        self.tts_service = tts_service or TTSService(
            api_key=api_key, audio_path=temp_audio_path, logger=self.logger
        )
        self.storage_service = storage_service or StorageService(logger=self.logger)

    async def _get_lecture_entities(
        self, course_code: str, week: int, number: int
    ) -> Tuple[Any, Lecture, Any]:
        """
        Get course, lecture, and professor entities needed for audio creation.

        Returns:
            Tuple of (course, lecture, professor)
        """
        # Get course
        course = self.repository.course.get_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Get lecture
        lecture = self.repository.lecture.get_by_course_week_order(
            course_id=course.id, week_number=week, order_in_week=number
        )
        if not lecture:
            error_msg = f"Lecture for course {course_code}, week {week}, number {number} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Get professor
        professor = self.repository.professor.get(course.professor_id)
        if not professor:
            error_msg = f"Professor with ID {course.professor_id} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        return course, lecture, professor

    def _get_professor_voice_id(self, professor) -> Optional[str]:
        """Get ElevenLabs voice ID for the professor if available."""
        if not professor.voice_id:
            return None

        voice_record = self.repository.voice.get(professor.voice_id)
        if not voice_record:
            return None

        el_voice_id = voice_record.el_voice_id
        self.logger.info(
            f"Using voice from database: {voice_record.name} ({el_voice_id})"
        )
        return el_voice_id

    async def _generate_and_store_audio(
        self,
        lecture,
        professor,
        course_code: str,
        week: int,
        number: int,
        el_voice_id: Optional[str],
    ) -> str:
        """Generate audio using TTS and store it. Returns storage URL."""
        # Generate audio using TTS service
        _, audio_data = self.tts_service.generate_lecture_audio(
            lecture=lecture,
            professor=professor,
            el_voice_id=el_voice_id,
        )

        # Upload to storage service (MinIO/S3)
        storage_key = self.storage_service.generate_audio_key(
            course_id=course_code, week_number=week, lecture_order=number
        )

        success, storage_url = await self.storage_service.upload_audio_file(
            file_data=audio_data, object_name=storage_key, content_type="audio/mpeg"
        )

        if not success:
            error_msg = "Failed to upload audio to storage"
            self.logger.error(error_msg)
            raise AudioProcessingError(error_msg)

        self.logger.info(f"Audio uploaded to storage at {storage_url}")
        return storage_url

    def _update_lecture_audio_url(self, lecture, audio_url: str) -> Lecture:
        """Update lecture with audio URL and return updated lecture."""
        lecture_to_update = self.repository.lecture.get(lecture.id)
        if not lecture_to_update:
            raise ValueError(f"Lecture with ID {lecture.id} not found")

        lecture_to_update.audio_url = audio_url
        updated_lecture = self.repository.lecture.update(lecture_to_update)
        self.logger.debug(f"Lecture updated with audio url: {audio_url}")
        return updated_lecture

    async def create_lecture_audio(
        self, course_code: str, week: int, number: int = 1
    ) -> Tuple[str, Lecture]:
        """
        Create audio for a lecture.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week

        Returns:
            Tuple: (audio_url, lecture) - URL to the audio file and the lecture
        """
        self.logger.info(
            f"Creating audio for course {course_code}, week {week}, number {number}"
        )

        try:
            # Get required entities
            course, lecture, professor = await self._get_lecture_entities(
                course_code, week, number
            )

            # Get voice ID if available
            el_voice_id = self._get_professor_voice_id(professor)

            # Generate and store audio
            audio_url = await self._generate_and_store_audio(
                lecture, professor, course_code, week, number, el_voice_id
            )

            # Update lecture with audio URL
            lecture = self._update_lecture_audio_url(lecture, audio_url)

            return audio_url, lecture

        except Exception as e:
            error_msg = f"Failed to create lecture audio: {str(e)}"
            self.logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

    def list_available_voices(self, **filters) -> List[Dict[str, Any]]:
        """
        List available voices with optional filtering.

        Args:
            **filters: Filter parameters (gender, accent, age)

        Returns:
            List of voices
        """
        client = self.tts_service.client
        voices, _ = client.get_shared_voices(**filters)

        # Map voice_id to el_voice_id to match database schema
        for voice in voices:
            if "voice_id" in voice and "el_voice_id" not in voice:
                voice["el_voice_id"] = voice["voice_id"]

        return voices

    def test_tts_connection(self) -> Dict[str, Any]:
        """
        Test connection to the TTS service.

        Returns:
            Connection status
        """
        return self.tts_service.test_connection()

    async def play_audio(self, audio_url: str):
        """
        Play audio from a storage URL.

        Args:
            audio_url: Storage URL of the audio file
        """
        # Check if it's a storage URL
        if not (audio_url.startswith("http://") or audio_url.startswith("https://")):
            # If it's not a URL, maybe it's a local path (for testing/debugging)
            if os.path.exists(audio_url):
                self.logger.info(f"Playing audio from local path: {audio_url}")
                self.tts_service.play_audio(audio_url)
                return
            else:
                error_msg = f"Invalid audio source: {audio_url}. Expected a URL or an existing local path."
                self.logger.error(error_msg)
                raise AudioProcessingError(error_msg)

        try:
            # Parse URL to attempt to extract bucket and object key
            parsed_url = urllib.parse.urlparse(audio_url)
            path_parts = parsed_url.path.strip("/").split("/", 1)

            if len(path_parts) == 2:
                bucket = path_parts[0]
                object_name = path_parts[1]

                self.logger.info(
                    f"Attempting to download audio from storage: bucket='{bucket}', key='{object_name}'"
                )
                # Download from storage
                audio_data, _ = await self.storage_service.download_file(
                    bucket, object_name
                )
                if audio_data:
                    self.logger.info("Audio downloaded successfully, playing...")
                    self.tts_service.play_audio(audio_data)
                else:
                    error_msg = f"Failed to download audio from storage: {audio_url}"
                    self.logger.error(error_msg)
                    raise AudioProcessingError(error_msg)
            else:
                error_msg = f"Could not parse bucket/key from URL: {audio_url}"
                self.logger.error(error_msg)
                raise AudioProcessingError(error_msg)
        except Exception as e:
            error_msg = f"Error processing storage URL {audio_url}: {e}"
            self.logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e
