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
from dataclasses import dataclass
from typing import Any, Dict, Optional

from artificial_u.audio.speech_processor import SpeechProcessor
from artificial_u.config import get_settings
from artificial_u.integrations.elevenlabs.models import FALLBACK_MODEL, UNGATED_MODELS
from artificial_u.integrations.tts.base import TTSBackend
from artificial_u.models.core import Lecture, Professor
from artificial_u.utils import AudioProcessingError

ELEVENLABS_MODEL_PREFERENCE = [
    "eleven_flash_v2_5",
    "eleven_v3",
    "eleven_multilingual_v2",
]


@dataclass(frozen=True)
class LectureAudio:
    """Synthesized lecture audio and the model that actually produced it."""

    audio: bytes
    model_id: Optional[str] = None


def configured_tts_model(backend_name: str, settings: Any = None) -> Optional[str]:
    """Model a backend is configured to use, or None when it isn't known up front.

    For ElevenLabs this is the preferred model; generation may still fall back to
    another one for a voice that can't use it.
    """
    settings = settings or get_settings()
    if backend_name == "elevenlabs":
        return settings.TTS_VOICE_MODEL
    if backend_name == "mistral":
        return settings.TTS_MISTRAL_MODEL
    return None


class TTSService:
    """Service for text-to-speech conversion with pluggable backends."""

    def __init__(
        self,
        backend: TTSBackend,
        speech_processor: Optional[SpeechProcessor] = None,
        repository_factory=None,
        logger=None,
    ):
        """
        Initialize the TTS service.

        Args:
            backend: TTS backend to use.
            speech_processor: Optional speech processor instance.
            repository_factory: Optional repository factory instance.
            logger: Optional logger instance.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.repository_factory = repository_factory
        self.speech_processor = speech_processor or SpeechProcessor(logger=self.logger)
        self.settings = get_settings()
        self.backend = backend

    def convert_text_to_speech(
        self,
        text: str,
        voice_id: str,
        chunk_size: int = 4000,
        language: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> bytes:
        """
        Convert text to speech using the configured backend.

        Args:
            text: Text to convert.
            voice_id: Provider-specific voice identifier.
            chunk_size: Maximum size of text chunks.
            language: Optional output language (BCP-47). Passed to backends that
                accept one (e.g. xAI); ignored by others.
            model_id: Optional model override (passed to backend).

        Returns:
            Audio data as bytes.
        """
        if not voice_id:
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
                    voice_id=voice_id,
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

    def synthesize_lecture_audio(
        self,
        lecture: Lecture,
        professor: Professor,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> LectureAudio:
        """
        Generate audio for a lecture.

        Args:
            lecture: Lecture to generate audio for.
            professor: Professor delivering the lecture.
            voice_id: Provider-specific voice identifier.
            model_id: Optional model override.
            language: Optional output language (BCP-47); passed to backends
                that accept one (e.g. xAI).

        Returns:
            The audio and the model that produced it (None if the backend's model
            isn't known).
        """
        effective_voice_id = voice_id or self._voice_id_for_professor(professor)

        # Resolve the best model this voice supports
        auto_model = self.backend.backend_name == "elevenlabs" and model_id is None
        if auto_model:
            model_id = self._resolve_model_for_voice(
                professor=professor,
                el_voice_id=effective_voice_id,
            )

        def convert(model: Optional[str]) -> LectureAudio:
            audio = self.convert_text_to_speech(
                text=lecture.content,
                voice_id=effective_voice_id,
                model_id=model,
                language=language,
            )
            used = model or configured_tts_model(self.backend.backend_name, self.settings)
            return LectureAudio(audio=audio, model_id=used)

        try:
            try:
                return convert(model_id)
            except Exception as e:
                if not (auto_model and model_id in UNGATED_MODELS):
                    raise
                # The voice may not be usable with the newer model; retry with the
                # model the voice is verified for.
                fallback = self._resolve_verified_model_for_voice(professor, effective_voice_id)
                self.logger.warning(
                    "Voice %s failed with %s (%s); retrying with %s",
                    effective_voice_id,
                    model_id,
                    e,
                    fallback,
                )
                return convert(fallback)
        except Exception as e:
            raise AudioProcessingError(f"Failed to generate lecture audio: {e}")

    def _voice_id_for_professor(self, professor: Professor) -> str:
        """Return the provider-specific voice ID for the professor's assigned voice."""
        if not (professor.voice_id and self.repository_factory):
            raise ValueError("No voice ID specified or found for professor")
        voice = self.repository_factory.voice.get(professor.voice_id)
        if not voice:
            raise ValueError("No voice found for professor")
        # Use el_voice_id for ElevenLabs, external_id for others
        if voice.tts_backend == "elevenlabs" and voice.el_voice_id:
            return voice.el_voice_id
        return voice.external_id or voice.el_voice_id

    def _resolve_model_for_voice(self, professor: Professor, el_voice_id: Optional[str]) -> str:
        """Return the ElevenLabs model to use for this voice.

        Ungated models (e.g. eleven_v4) configured via TTS_VOICE_MODEL work with
        any library voice, so they are used as-is; generation retries with
        ``_resolve_verified_model_for_voice`` if the voice turns out not to work.
        """
        configured = self.settings.TTS_VOICE_MODEL
        if configured in UNGATED_MODELS:
            return configured
        return self._resolve_verified_model_for_voice(professor, el_voice_id)

    def _resolve_verified_model_for_voice(
        self, professor: Professor, el_voice_id: Optional[str]
    ) -> str:
        """Return the best ElevenLabs model this voice is verified for.

        Checks verified_languages from the DB record (or the ElevenLabs API as
        a fallback) and returns the first match from ELEVENLABS_MODEL_PREFERENCE.
        Falls back to TTS_VOICE_MODEL (or FALLBACK_MODEL if that is an ungated
        model) when no model info is available.
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

        configured = self.settings.TTS_VOICE_MODEL
        return FALLBACK_MODEL if configured in UNGATED_MODELS else configured
