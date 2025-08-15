"""
Text-to-Speech service for ArtificialU.

This service handles converting text to speech using ElevenLabs.
"""

import logging
import os
from typing import Any, Dict, Optional, Union

from artificial_u.audio.speech_processor import SpeechProcessor
from artificial_u.config import get_settings
from artificial_u.integrations import elevenlabs
from artificial_u.models.core import Lecture, Professor
from artificial_u.utils import AudioProcessingError


class TTSService:
    """Service for text-to-speech conversion."""

    # Model selection is driven by settings.TTS_VOICE_MODEL

    # Default voice settings
    DEFAULT_VOICE_SETTINGS = {
        "similarity_boost": 0.0,
        "speed": 1.0,
        "stability": 0.5,
        "style": 0.0,
        "use_speaker_boost": True,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[elevenlabs.ElevenLabsClient] = None,
        speech_processor: Optional[SpeechProcessor] = None,
        repository_factory=None,
        logger=None,
    ):
        """
        Initialize the TTS service.

        Args:
            api_key: Optional ElevenLabs API key
            client: Optional ElevenLabs client instance
            speech_processor: Optional speech processor instance
            repository_factory: Optional repository factory instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository_factory = repository_factory

        # Initialize components
        self.client = client or elevenlabs.ElevenLabsClient(api_key=api_key)
        self.speech_processor = speech_processor or SpeechProcessor(logger=self.logger)
        # Load settings for global TTS model
        self.settings = get_settings()

    def convert_text_to_speech(
        self,
        text: str,
        el_voice_id: str,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
        chunk_size: int = 4000,
    ) -> bytes:
        """
        Convert text to speech.

        Args:
            text: Text to convert
            el_voice_id: ElevenLabs Voice ID to use
            model_id: Optional model ID (defaults to eleven_flash_v2_5)
            voice_settings: Optional voice settings
            chunk_size: Maximum size of text chunks

        Returns:
            Audio data as bytes
        """
        model_id = model_id or getattr(self.settings, "TTS_VOICE_MODEL")
        voice_settings = voice_settings or self.DEFAULT_VOICE_SETTINGS.copy()

        # Prefer normalized plain text for TTS requests to avoid SSML-like tags
        # Some models (e.g., flash v2.5) can mis-handle embedded markup
        normalized_text = self.speech_processor.normalize_text(text)

        # Split text into chunks if necessary
        chunks = self.speech_processor.split_into_chunks(normalized_text, max_chunk_size=chunk_size)

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
                    voice_id=el_voice_id,
                    model_id=model_id,
                    voice_settings=voice_settings,
                )

                audio_segments.append(audio_data)
                if len(audio_data) < 16000 and len(chunk) > 500:
                    self.logger.warning(
                        "Chunk %d produced very small audio (%d bytes).",
                        i + 1,
                        len(audio_data),
                    )
                self.logger.info(f"Successfully processed chunk {i+1}")
            except Exception as e:
                self.logger.error(f"Error processing chunk {i+1}: {e}")
                raise AudioProcessingError(f"Failed to convert chunk {i+1} to speech: {e}")

        # Combine audio segments
        if not audio_segments:
            raise AudioProcessingError("No audio segments were generated")

        audio = b"".join(audio_segments)
        return audio

    def generate_lecture_audio(
        self,
        lecture: Lecture,
        professor: Professor,
        el_voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> bytes:
        """
        Generate audio for a lecture.

        Args:
            lecture: Lecture to generate audio for
            professor: Professor delivering the lecture
            el_voice_id: Optional ElevenLabs voice ID (will be selected if not provided)
            model_id: Optional ElevenLabs model ID

        Returns:
            Tuple of (file path or empty string, audio data)
        """
        # Get voice ID from professor if not specified
        if not el_voice_id:
            if (
                professor.voice_id
                and hasattr(self, "repository_factory")
                and self.repository_factory
            ):
                # Look up the voice in the database
                voice = self.repository_factory.voice.get(professor.voice_id)
                if voice:
                    el_voice_id = voice.el_voice_id
                else:
                    raise ValueError("No voice ID specified or found for professor")
                # TODO: Maybe use select_voice_for_professor here?
            else:
                raise ValueError("No voice ID specified or found for professor")

        # Resolve model id from settings if not provided
        model_id = model_id or getattr(self.settings, "TTS_VOICE_MODEL")

        # Verify voice supports the chosen model when we can fetch metadata
        self._validate_voice_model_support(
            professor=professor, el_voice_id=el_voice_id, model_id=model_id
        )

        # Generate the audio
        try:
            audio_data = self.convert_text_to_speech(
                text=lecture.content,
                el_voice_id=el_voice_id,
                model_id=model_id,
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to generate lecture audio: {e}")

        return audio_data

    def _validate_voice_model_support(
        self, professor: Professor, el_voice_id: Optional[str], model_id: str
    ) -> None:
        """Raise if the selected voice does not support the configured model."""
        try:
            voice_info = (
                self.repository_factory.voice.get(professor.voice_id)
                if professor.voice_id
                else None
            )
            if not voice_info and el_voice_id:
                # Fetch minimal details from API when DB is missing
                voice_info = self.client.get_el_voice(el_voice_id)

            verified = None
            if voice_info and isinstance(voice_info, dict):
                verified = voice_info.get("verified_languages")
            elif voice_info and hasattr(voice_info, "model_dump"):
                verified = voice_info.model_dump().get("verified_languages")

            if verified and isinstance(verified, list):
                model_ids = {item.get("model_id") for item in verified if isinstance(item, dict)}
                if model_ids and model_id not in model_ids:
                    supported = ", ".join(sorted(m for m in model_ids if m))
                    msg = (
                        f"Voice does not support model '{model_id}'. "
                        f"Supported models: {supported}"
                    )
                    raise AudioProcessingError(msg)
        except AudioProcessingError:
            raise
        except Exception:
            # Non-fatal: if verification fails, continue and let API decide
            return

    def play_audio(self, audio_source: Union[bytes, str]) -> None:
        """
        Play audio data or a file.

        Args:
            audio_source: Audio data as bytes or path to an audio file
        """
        # If audio_source is a file path, read the file
        if isinstance(audio_source, str) and os.path.exists(audio_source):
            try:
                with open(audio_source, "rb") as f:
                    audio_data = f.read()
            except Exception as e:
                raise AudioProcessingError(f"Failed to read audio file {audio_source}: {e}")
        elif isinstance(audio_source, bytes):
            audio_data = audio_source
        else:
            raise TypeError("audio_source must be bytes or a string path to an existing file")

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
