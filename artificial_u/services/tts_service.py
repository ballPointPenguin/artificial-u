"""
Text-to-Speech service for ArtificialU.

This service handles converting text to speech using pluggable TTS backends.
Defaults to ElevenLabs but supports Mistral and other providers.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, Optional, Union

from artificial_u.audio.speech_processor import SpeechProcessor
from artificial_u.config import get_settings
from artificial_u.integrations.tts.base import TTSBackend
from artificial_u.models.core import Lecture, Professor
from artificial_u.utils import AudioProcessingError


class TTSService:
    """Service for text-to-speech conversion with pluggable backends."""

    def __init__(
        self,
        backend: Optional[TTSBackend] = None,
        speech_processor: Optional[SpeechProcessor] = None,
        repository_factory=None,
        logger=None,
        # Legacy kwargs for backward compatibility
        api_key: Optional[str] = None,
        client=None,
    ):
        """
        Initialize the TTS service.

        Args:
            backend: TTS backend to use. If not provided, creates an ElevenLabs
                backend using api_key or settings.
            speech_processor: Optional speech processor instance.
            repository_factory: Optional repository factory instance.
            logger: Optional logger instance.
            api_key: Legacy param - ElevenLabs API key (used if backend is None).
            client: Legacy param - ElevenLabsClient instance (used if backend is None).
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository_factory = repository_factory
        self.speech_processor = speech_processor or SpeechProcessor(logger=self.logger)
        self.settings = get_settings()

        # Resolve the backend
        if backend is not None:
            self.backend = backend
        elif client is not None:
            # Legacy path: wrap an existing ElevenLabsClient
            from artificial_u.integrations.tts.elevenlabs_backend import ElevenLabsTTSBackend

            self.backend = ElevenLabsTTSBackend(client=client, logger=self.logger)
        else:
            # Default: create backend from settings
            from artificial_u.integrations.tts.factory import create_tts_backend

            self.backend = create_tts_backend(
                backend_name="elevenlabs",
                api_key=api_key,
                logger=self.logger,
            )

    def convert_text_to_speech(
        self,
        text: str,
        voice_id: str,
        chunk_size: int = 4000,
        # Legacy kwargs preserved for backward compatibility
        el_voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
    ) -> bytes:
        """
        Convert text to speech using the configured backend.

        Args:
            text: Text to convert.
            voice_id: Provider-specific voice identifier.
            chunk_size: Maximum size of text chunks.
            el_voice_id: Legacy alias for voice_id.
            model_id: Optional model override (passed to backend).
            voice_settings: Optional voice settings (passed to backend).

        Returns:
            Audio data as bytes.
        """
        # Support legacy callers passing el_voice_id
        effective_voice_id = voice_id or el_voice_id
        if not effective_voice_id:
            raise ValueError("voice_id is required")

        # Normalize text, skipping SSML if backend doesn't support it
        if self.backend.supports_ssml():
            normalized_text = self.speech_processor.normalize_text(text)
        else:
            normalized_text = self.speech_processor.normalize_text(text, supports_ssml=False)

        # Split text into chunks if necessary
        chunks = self.speech_processor.split_into_chunks(normalized_text, max_chunk_size=chunk_size)

        # Generate audio for each chunk
        audio_segments = []
        total_chunks = len(chunks)
        self.logger.info(
            "Converting text to speech in %d chunks via %s",
            total_chunks,
            self.backend.backend_name,
        )

        # Build backend-specific kwargs
        backend_kwargs: Dict[str, Any] = {}
        if model_id:
            backend_kwargs["model_id"] = model_id
        if voice_settings:
            backend_kwargs["voice_settings"] = voice_settings

        for i, chunk in enumerate(chunks):
            chunk_len = len(chunk)
            word_count = len(chunk.split())
            self.logger.info(
                "Processing chunk %d/%d (%d chars, %d words)",
                i + 1,
                total_chunks,
                chunk_len,
                word_count,
            )

            if not self.speech_processor.is_valid_chunk(chunk):
                self.logger.warning("Skipping invalid chunk %d: too short or empty", i + 1)
                continue

            try:
                audio_data = self.backend.text_to_speech(
                    text=chunk,
                    voice_id=effective_voice_id,
                    **backend_kwargs,
                )
                audio_segments.append(audio_data)
                if len(audio_data) < 16000 and chunk_len > 500:
                    self.logger.warning(
                        "Chunk %d produced very small audio (%d bytes).",
                        i + 1,
                        len(audio_data),
                    )
                self.logger.info("Successfully processed chunk %d", i + 1)
            except Exception as e:
                self.logger.error("Error processing chunk %d: %s", i + 1, e)
                raise AudioProcessingError(f"Failed to convert chunk {i + 1} to speech: {e}")

        if not audio_segments:
            raise AudioProcessingError("No audio segments were generated")

        audio = b"".join(audio_segments)

        # Fix MP3 headers if multiple segments were concatenated
        if len(audio_segments) > 1:
            audio = self._fix_mp3_headers(audio)

        return audio

    def _fix_mp3_headers(self, audio_data: bytes) -> bytes:
        """
        Fix MP3 headers after concatenating multiple audio segments.

        When MP3 files are concatenated by joining bytes directly, the resulting
        file has invalid headers - the first segment's duration metadata is used
        for the entire file, causing players to show incorrect duration and
        preventing seeking past the first segment's length.

        This uses ffmpeg to re-mux the audio stream, which fixes the headers
        without re-encoding the audio data.
        """
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            self.logger.warning(
                "ffmpeg not found - skipping MP3 header fix. "
                "Audio may have incorrect duration metadata."
            )
            return audio_data

        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="tts_mp3_fix_")
            input_path = os.path.join(temp_dir, "input.mp3")
            output_path = os.path.join(temp_dir, "output.mp3")

            with open(input_path, "wb") as f:
                f.write(audio_data)

            cmd = [
                ffmpeg_path,
                "-y",
                "-i",
                input_path,
                "-c:a",
                "copy",
                "-write_xing",
                "0",
                output_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                self.logger.warning(
                    "ffmpeg header fix failed (exit %d): %s",
                    result.returncode,
                    result.stderr,
                )
                return audio_data

            with open(output_path, "rb") as f:
                fixed_audio = f.read()

            self.logger.info(
                "Fixed MP3 headers: %d -> %d bytes", len(audio_data), len(fixed_audio)
            )
            return fixed_audio

        except subprocess.TimeoutExpired:
            self.logger.warning("ffmpeg header fix timed out")
            return audio_data
        except Exception as e:
            self.logger.warning("Error fixing MP3 headers: %s", e)
            return audio_data
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.debug("Error cleaning up temp dir: %s", e)

    def generate_lecture_audio(
        self,
        lecture: Lecture,
        professor: Professor,
        voice_id: Optional[str] = None,
        el_voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> bytes:
        """
        Generate audio for a lecture.

        Args:
            lecture: Lecture to generate audio for.
            professor: Professor delivering the lecture.
            voice_id: Provider-specific voice identifier.
            el_voice_id: Legacy alias for voice_id (ElevenLabs voice ID).
            model_id: Optional model override.

        Returns:
            Audio data as bytes.
        """
        effective_voice_id = voice_id or el_voice_id

        # Resolve voice from professor if not specified
        if not effective_voice_id:
            if professor.voice_id and self.repository_factory:
                voice = self.repository_factory.voice.get(professor.voice_id)
                if voice:
                    # Use el_voice_id for ElevenLabs, external_id for others
                    if voice.tts_backend == "elevenlabs" and voice.el_voice_id:
                        effective_voice_id = voice.el_voice_id
                    elif voice.external_id:
                        effective_voice_id = voice.external_id
                    else:
                        effective_voice_id = voice.el_voice_id
                else:
                    raise ValueError("No voice found for professor")
            else:
                raise ValueError("No voice ID specified or found for professor")

        # ElevenLabs-specific validation
        if self.backend.backend_name == "elevenlabs":
            self._validate_voice_model_support(
                professor=professor,
                el_voice_id=effective_voice_id,
                model_id=model_id or self.settings.TTS_VOICE_MODEL,
            )

        try:
            audio_data = self.convert_text_to_speech(
                text=lecture.content,
                voice_id=effective_voice_id,
                model_id=model_id,
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to generate lecture audio: {e}")

        return audio_data

    def _validate_voice_model_support(
        self, professor: Professor, el_voice_id: Optional[str], model_id: str
    ) -> None:
        """Raise if the selected ElevenLabs voice does not support the configured model."""
        try:
            voice_info = (
                self.repository_factory.voice.get(professor.voice_id)
                if professor.voice_id and self.repository_factory
                else None
            )
            if not voice_info and el_voice_id:
                # Fetch minimal details from ElevenLabs API
                if hasattr(self.backend, "client"):
                    voice_info = self.backend.client.get_el_voice(el_voice_id)

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
            return

    def play_audio(self, audio_source: Union[bytes, str]) -> None:
        """Play audio data or a file."""
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

        # play_audio is ElevenLabs-specific
        if hasattr(self.backend, "client") and hasattr(self.backend.client, "play_audio"):
            try:
                self.backend.client.play_audio(audio_data)
            except Exception as e:
                raise AudioProcessingError(f"Failed to play audio: {e}")
        else:
            self.logger.warning("play_audio not supported by %s backend", self.backend.backend_name)

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the TTS service."""
        if hasattr(self.backend, "client") and hasattr(self.backend.client, "test_connection"):
            return self.backend.client.test_connection()
        return {"status": "ok", "backend": self.backend.backend_name}
