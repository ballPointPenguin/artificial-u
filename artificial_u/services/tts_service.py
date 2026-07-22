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

ELEVENLABS_MODEL_PREFERENCE = [
    "eleven_flash_v2_5",
    "eleven_v3",
    "eleven_multilingual_v2",
]


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
                backend_name=self.settings.tts_backend or "elevenlabs",
                api_key=api_key,
                logger=self.logger,
            )

    def convert_text_to_speech(
        self,
        text: str,
        voice_id: str,
        chunk_size: int = 4000,
        language: Optional[str] = None,
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
            language: Optional output language (BCP-47). Passed to backends that
                accept one (e.g. xAI); ignored by others.
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

        # Normalize text using the explicit per-backend processing path.
        normalized_text = self.speech_processor.normalize_text(
            text, backend_name=self.backend.backend_name
        )

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
        if language:
            # Backends that don't accept a language kwarg ignore it (they read
            # only their own keys from **kwargs).
            backend_kwargs["language"] = language

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

        # Always remux so the output has a fresh, accurate Xing/Info header
        # describing the full file. This matters even for single-segment output
        # because some providers ship raw frames or a header that only describes
        # a partial stream. Without a trustworthy Xing header, readers fall back
        # to CBR extrapolation and report wildly wrong durations (browsers end
        # up "chasing" the playhead, Finder/mutagen read short values, and
        # scrubbing maps to wrong real-time positions).
        audio = self._fix_mp3_headers(audio)

        return audio

    def _fix_mp3_headers(self, audio_data: bytes) -> bytes:
        """
        Re-mux an MP3 so it has a correct Xing/Info header.

        MP3 has no file-level duration field; readers rely on the Xing header
        tucked into the first MPEG frame (total frames + total bytes + TOC) to
        know the duration accurately. When we concatenate per-chunk MP3s from
        a TTS backend, the inherited Xing from chunk 1 no longer describes the
        whole file, and single-chunk responses may not include a Xing at all.

        We use ffmpeg with stream copy (no re-encoding), letting the MP3 muxer
        regenerate the Xing header from the actual frame count. This is the
        default behavior - do NOT pass `-write_xing 0` here, it would strip
        the header and leave downstream readers guessing via CBR extrapolation.
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

            self.logger.info("Fixed MP3 headers: %d -> %d bytes", len(audio_data), len(fixed_audio))
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
        language: Optional[str] = None,
    ) -> bytes:
        """
        Generate audio for a lecture.

        Args:
            lecture: Lecture to generate audio for.
            professor: Professor delivering the lecture.
            voice_id: Provider-specific voice identifier.
            el_voice_id: Legacy alias for voice_id (ElevenLabs voice ID).
            model_id: Optional model override.
            language: Optional output language (BCP-47); passed to backends
                that accept one (e.g. xAI).

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

        # Resolve the best model this voice supports
        if self.backend.backend_name == "elevenlabs" and model_id is None:
            model_id = self._resolve_model_for_voice(
                professor=professor,
                el_voice_id=effective_voice_id,
            )

        try:
            audio_data = self.convert_text_to_speech(
                text=lecture.content,
                voice_id=effective_voice_id,
                model_id=model_id,
                language=language,
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to generate lecture audio: {e}")

        return audio_data

    def _resolve_model_for_voice(self, professor: Professor, el_voice_id: Optional[str]) -> str:
        """Return the best ElevenLabs model supported by this voice.

        Checks verified_languages from the DB record (or the ElevenLabs API as
        a fallback) and returns the first match from ELEVENLABS_MODEL_PREFERENCE.
        Falls back to TTS_VOICE_MODEL when no model info is available.
        """
        try:
            voice_info = (
                self.repository_factory.voice.get(professor.voice_id)
                if professor.voice_id and self.repository_factory
                else None
            )
            if not voice_info and el_voice_id and hasattr(self.backend, "client"):
                voice_info = self.backend.client.get_el_voice(el_voice_id)

            verified = None
            if voice_info and isinstance(voice_info, dict):
                verified = voice_info.get("verified_languages")
            elif voice_info and hasattr(voice_info, "model_dump"):
                verified = voice_info.model_dump().get("verified_languages")

            if verified and isinstance(verified, list):
                supported = {item.get("model_id") for item in verified if isinstance(item, dict)}
                supported.discard(None)
                if supported:
                    for model in ELEVENLABS_MODEL_PREFERENCE:
                        if model in supported:
                            if model != self.settings.TTS_VOICE_MODEL:
                                self.logger.info(
                                    "Voice supports %s (not %s); using %s",
                                    model,
                                    self.settings.TTS_VOICE_MODEL,
                                    model,
                                )
                            return model
                    # No preferred model supported — use whatever the voice does support
                    fallback = next(iter(supported))
                    self.logger.warning(
                        "Voice does not support any preferred model %s; falling back to %s",
                        ELEVENLABS_MODEL_PREFERENCE,
                        fallback,
                    )
                    return fallback
        except Exception as e:
            self.logger.debug("Could not resolve voice model info: %s", e)

        return self.settings.TTS_VOICE_MODEL

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
