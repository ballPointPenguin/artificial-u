"""
Pydantic models for Voice API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VoiceBase(BaseModel):
    tts_backend: str = Field("elevenlabs", description="TTS backend provider (e.g., elevenlabs)")
    external_id: Optional[str] = Field(None, description="Provider-specific voice identifier")
    el_voice_id: Optional[str] = Field(None, description="ElevenLabs Voice ID (legacy)")
    name: Optional[str] = Field(None, description="Name of the voice")
    accent: Optional[str] = Field(None, description="Accent of the voice")
    age: Optional[str] = Field(None, description="Age category of the voice")
    category: Optional[str] = Field(
        None, description="Category of the voice (e.g., professional, conversational)"
    )
    description: Optional[str] = Field(None, description="Description of the voice")
    descriptive: Optional[str] = Field(None, description="Descriptive tags for the voice")
    gender: Optional[str] = Field(None, description="Gender of the voice")
    language: Optional[str] = Field(None, description="Language of the voice")
    locale: Optional[str] = Field(None, description="Locale of the voice")
    popularity_score: Optional[int] = Field(
        None, description="Popularity score (e.g., cloned_by_count or usage_character_count_1y)"
    )
    preview_url: Optional[str] = Field(None, description="URL to preview the voice")
    use_case: Optional[str] = Field(None, description="Intended use case for the voice")
    verified_languages: List[Dict[str, Any]] = Field(
        default_factory=list, description="Verified languages for the voice"
    )
    cloned_from: Optional[int] = Field(
        None, description="ID of the source voice this was cloned from, if any"
    )


class VoiceResponse(VoiceBase):
    id: int = Field(..., description="Database ID of the voice")
    last_updated: Optional[datetime] = Field(
        None, description="Last time the voice record was updated in the database"
    )

    class Config:
        from_attributes = True


class VoiceListResponse(BaseModel):
    items: List[VoiceResponse] = Field(..., description="List of voices")
    total: int = Field(..., description="Total number of matching voices")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class VoiceDesignPreview(BaseModel):
    """A single audio preview returned by the ElevenLabs Voice Design API."""

    generated_voice_id: str = Field(
        ..., description="Temporary voice ID; valid only until saved to the library"
    )
    audio_sample: str = Field(..., description="Base64-encoded MP3 audio sample")
    media_type: str = Field("audio/mpeg", description="MIME type of the audio sample")
    duration_secs: Optional[float] = Field(None, description="Duration of the audio sample")
    voice_description: str = Field(..., description="The Voice Design prompt that was used")


class VoiceDesignPreviewsResponse(BaseModel):
    """Response containing multiple Voice Design previews for a professor."""

    previews: List[VoiceDesignPreview]


class VoiceDesignSaveRequest(BaseModel):
    """Request to save a selected Voice Design preview and assign it to a professor."""

    professor_id: int = Field(..., description="Database ID of the professor")
    generated_voice_id: str = Field(..., description="Temporary ID from the Voice Design preview")
    voice_name: str = Field(..., description="Name to give the saved voice in the library")
    voice_description: str = Field(
        ..., description="The Voice Design prompt (stored as the voice description)"
    )


class VoiceCloneToMistralRequest(BaseModel):
    """Request to clone a professor's current ElevenLabs voice into Mistral."""

    professor_id: int = Field(..., description="Database ID of the professor")


class ManualVoiceAssignmentRequest(BaseModel):
    external_id: Optional[str] = Field(None, description="Provider-specific voice identifier")
    tts_backend: str = Field(
        "elevenlabs", description="TTS backend for the voice (e.g., elevenlabs, mistral)"
    )
    # Legacy alias — accepted for backward compatibility
    el_voice_id: Optional[str] = Field(
        None, description="ElevenLabs Voice ID (legacy, use external_id instead)"
    )
