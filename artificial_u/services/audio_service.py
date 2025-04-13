"""
Audio processing service for ArtificialU.
"""

import logging
import os
from typing import Optional, Tuple, Dict, Any, List
import urllib.parse

from artificial_u.models.core import Lecture
from artificial_u.utils.exceptions import AudioProcessingError
from artificial_u.services.voice_service import VoiceService
from artificial_u.services.tts_service import TTSService
from artificial_u.services.storage_service import StorageService


class AudioService:
    """Service for processing audio in ArtificialU."""

    def __init__(
        self,
        repository,
        api_key: Optional[str] = None,
        voice_service: Optional[VoiceService] = None,
        tts_service: Optional[TTSService] = None,
        storage_service: Optional[StorageService] = None,
        logger=None,
    ):
        """
        Initialize the audio service.

        Args:
            repository: Data repository
            api_key: Optional ElevenLabs API key
            voice_service: Optional voice service instance
            tts_service: Optional TTS service instance
            storage_service: Optional storage service instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository = repository

        # Initialize services (TTS service still needs temp path)
        # Get temp path from storage service's settings
        storage_settings = (storage_service or StorageService()).settings
        temp_audio_path = storage_settings.TEMP_AUDIO_PATH

        self.voice_service = voice_service or VoiceService(
            api_key=api_key, logger=self.logger
        )
        self.tts_service = tts_service or TTSService(
            api_key=api_key, audio_path=temp_audio_path, logger=self.logger
        )
        self.storage_service = storage_service or StorageService(logger=self.logger)

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
            if not professor.voice_id:
                # Select a voice and update professor record
                voice_data = self.voice_service.select_voice_for_professor(professor)

                # Update local professor object with the db voice ID
                if "db_voice_id" in voice_data:
                    professor.voice_id = voice_data["db_voice_id"]
                    # Use the ElevenLabs voice ID
                    el_voice_id = voice_data["voice_id"]
                else:
                    raise ValueError("Failed to assign voice to professor")
            else:
                # Use professor.voice_id to get the voice record from db, use its el_voice_id
                voice_record = self.repository.get_voice(professor.voice_id)
                if not voice_record:
                    raise ValueError(f"Voice with ID {professor.voice_id} not found")
                el_voice_id = voice_record.el_voice_id

            # Generate audio using TTS service
            # The TTS service might still use a local temp file, but we get the bytes
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
                error_msg = f"Failed to upload audio to storage"
                self.logger.error(error_msg)
                raise AudioProcessingError(error_msg)

            # Set the audio url to the storage URL
            audio_url = storage_url

            self.logger.info(f"Audio uploaded to storage at {storage_url}")

        except Exception as e:
            error_msg = f"Failed to generate audio: {str(e)}"
            self.logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

        # Update lecture with audio url
        try:
            # Get the lecture first
            lecture_to_update = self.repository.get_lecture(lecture.id)
            if not lecture_to_update:
                raise ValueError(f"Lecture with ID {lecture.id} not found")

            # Update the audio path
            lecture_to_update.audio_url = audio_url  # Renamed from audio_path

            # Use the general update_lecture method
            lecture = self.repository.update_lecture(lecture_to_update)
            self.logger.debug(f"Lecture updated with audio url: {audio_url}")
        except Exception as e:
            error_msg = f"Failed to update lecture with audio url: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e

        return audio_url, lecture

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
