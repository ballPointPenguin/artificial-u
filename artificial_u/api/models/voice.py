"""
Pydantic models for Voice API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VoiceBase(BaseModel):
    el_voice_id: Optional[str] = Field(None, description="ElevenLabs Voice ID")
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
    verified_languages: Optional[Dict[str, Any]] = Field(
        None, description="Verified languages for the voice"
    )


class VoiceResponse(VoiceBase):
    id: int = Field(..., description="Database ID of the voice")
    last_updated: Optional[datetime] = Field(
        None, description="Last time the voice record was updated in the database"
    )

    class Config:
        orm_mode = True


class PaginatedVoiceResponse(BaseModel):
    items: List[VoiceResponse]
    total: int
    limit: int
    offset: int


class ManualVoiceAssignmentRequest(BaseModel):
    el_voice_id: str = Field(..., description="ElevenLabs Voice ID to assign")
