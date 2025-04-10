"""
Text-to-Speech service for ArtificialU.

This service handles converting text to speech using ElevenLabs.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union

from artificial_u.models.core import Lecture, Professor
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.audio.speech_processor import SpeechProcessor
from artificial_u.audio.audio_utils import AudioUtils
from artificial_u.utils.exceptions import AudioProcessingError


class TTSService:
    """Service for text-to-speech conversion."""

    # Default model for text-to-speech
    DEFAULT_MODEL = "eleven_flash_v2_5"

    # Default voice settings
    DEFAULT_VOICE_SETTINGS = {
        "stability": 0.5,
        "clarity": 0.8,
        "style": 0.0,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        audio_path: Optional[str] = None,
        client: Optional[ElevenLabsClient] = None,
        speech_processor: Optional[SpeechProcessor] = None,
        audio_utils: Optional[AudioUtils] = None,
        logger=None,
    ):
        """
        Initialize the TTS service.

        Args:
            api_key: Optional ElevenLabs API key
            audio_path: Optional base path for audio files
            client: Optional ElevenLabs client instance
            speech_processor: Optional speech processor instance
            audio_utils: Optional audio utilities instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize components
        self.client = client or ElevenLabsClient(api_key=api_key)
        self.speech_processor = speech_processor or SpeechProcessor(logger=self.logger)
        self.audio_utils = audio_utils or AudioUtils(
            base_audio_path=audio_path, logger=self.logger
        )

    def convert_text_to_speech(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
        chunk_size: int = 4000,
    ) -> bytes:
        """
        Convert text to speech.

        Args:
            text: Text to convert
            voice_id: Voice ID to use
            model_id: Optional model ID (defaults to eleven_flash_v2_5)
            voice_settings: Optional voice settings
            chunk_size: Maximum size of text chunks

        Returns:
            Audio data as bytes
        """
        model_id = model_id or self.DEFAULT_MODEL
        voice_settings = voice_settings or self.DEFAULT_VOICE_SETTINGS.copy()

        # Enhance text for better speech
        enhanced_text = self.speech_processor.enhance_speech_markup(text)

        # Split text into chunks if necessary
        chunks = self.speech_processor.split_lecture_into_chunks(
            enhanced_text, max_chunk_size=chunk_size
        )

        # Generate audio for each chunk
        audio_segments = []
        total_chunks = len(chunks)

        self.logger.info(f"Converting text to speech in {total_chunks} chunks")

        for i, chunk in enumerate(chunks):
            chunk_size = len(chunk)
            word_count = len(chunk.split())
            self.logger.info(
                f"Processing chunk {i+1}/{total_chunks} ({chunk_size} chars, {word_count} words)"
            )

            # Skip invalid chunks
            if not self.speech_processor.is_valid_chunk(chunk):
                self.logger.warning(f"Skipping invalid chunk {i+1}: too short or empty")
                continue

            # Generate audio
            try:
                audio_data = self.client.text_to_speech(
                    text=chunk,
                    voice_id=voice_id,
                    model_id=model_id,
                    voice_settings=voice_settings,
                )

                audio_segments.append(audio_data)
                self.logger.info(f"Successfully processed chunk {i+1}")
            except Exception as e:
                self.logger.error(f"Error processing chunk {i+1}: {e}")
                raise AudioProcessingError(
                    f"Failed to convert chunk {i+1} to speech: {e}"
                )

        # Combine audio segments
        if len(audio_segments) > 1:
            self.logger.info(f"Combining {len(audio_segments)} audio segments")
            audio = b"".join(audio_segments)
        elif audio_segments:
            audio = audio_segments[0]
        else:
            raise AudioProcessingError("No audio segments were generated")

        return audio

    def generate_lecture_audio(
        self,
        lecture: Lecture,
        professor: Professor,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        save_to_file: bool = True,
    ) -> Tuple[str, bytes]:
        """
        Generate audio for a lecture.

        Args:
            lecture: Lecture to generate audio for
            professor: Professor delivering the lecture
            voice_id: Optional voice ID (defaults to professor's voice settings)
            model_id: Optional model ID
            save_to_file: Whether to save audio to file

        Returns:
            Tuple of (file path or empty string, audio data)
        """
        # Get voice ID from professor if not specified
        if not voice_id:
            if professor.voice_settings and "voice_id" in professor.voice_settings:
                voice_id = professor.voice_settings["voice_id"]
            else:
                raise ValueError("No voice ID specified or found in professor settings")

        # Get voice settings from professor if available
        voice_settings = None
        if professor.voice_settings:
            settings = {}
            for key in ["stability", "clarity", "style"]:
                if key in professor.voice_settings:
                    settings[key] = professor.voice_settings[key]
            if settings:
                voice_settings = settings

        # Generate the audio
        try:
            audio_data = self.convert_text_to_speech(
                text=lecture.content,
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to generate lecture audio: {e}")

        # Save to file if requested
        file_path = ""
        if save_to_file:
            file_path = self.audio_utils.get_lecture_audio_path(
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                lecture_order=lecture.order_in_week,
            )

            try:
                self.audio_utils.save_audio_file(file_path, audio_data)
            except Exception as e:
                self.logger.error(f"Failed to save audio file: {e}")
                # Continue without saving

        return file_path, audio_data

    def play_audio(self, audio_data: Union[bytes, str]) -> None:
        """
        Play audio data or file.

        Args:
            audio_data: Audio data as bytes or file path
        """
        # If audio_data is a file path, read the file
        if isinstance(audio_data, str):
            try:
                audio_data = self.audio_utils.read_audio_file(audio_data)
            except Exception as e:
                raise AudioProcessingError(f"Failed to read audio file: {e}")

        # Play the audio
        try:
            self.client.play_audio(audio_data)
        except Exception as e:
            raise AudioProcessingError(f"Failed to play audio: {e}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the TTS service.

        Returns:
            Connection status information
        """
        return self.client.test_connection()
