"""
TTS backend protocol definition.

All TTS providers must implement this interface.
"""

from typing import Any, Dict, Optional, Protocol


class TTSBackend(Protocol):
    """Interface that all TTS backends must implement."""

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        **kwargs: Any,
    ) -> bytes:
        """Convert text to audio bytes.

        Args:
            text: Text to convert to speech.
            voice_id: Provider-specific voice identifier.
                For ElevenLabs: the el_voice_id.
                For Mistral: a preset voice name (e.g., "casual_male").
            **kwargs: Provider-specific options (model_id, voice_settings, etc.)

        Returns:
            Audio data as bytes (MP3 format preferred).
        """
        ...

    @property
    def backend_name(self) -> str:
        """Return the backend identifier (e.g., 'elevenlabs', 'mistral')."""
        ...

    @property
    def default_voice_settings(self) -> Dict[str, Any]:
        """Return default voice settings for this backend."""
        ...

    def supports_ssml(self) -> bool:
        """Whether this backend supports SSML-like markup (e.g., <break> tags)."""
        ...
