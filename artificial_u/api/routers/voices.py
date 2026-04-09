"""
API router for voice-related operations.
"""

import base64
import logging
from math import ceil
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from artificial_u.api.dependencies import get_tts_backend, get_voice_service
from artificial_u.api.models.voice import (
    ManualVoiceAssignmentRequest,
    VoiceListResponse,
    VoiceResponse,
)
from artificial_u.api.security.auth0 import require_auth
from artificial_u.integrations.tts import TTSBackend, create_tts_backend
from artificial_u.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/voices",
    tags=["voices"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{professor_id}/assign_voice", status_code=204, dependencies=[Depends(require_auth)])
async def manual_assign_voice(
    professor_id: str = Path(..., description="ID of the professor to assign voice to"),
    assignment_request: ManualVoiceAssignmentRequest = Body(...),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    Manually assign a voice to a professor.

    Accepts either `external_id` + `tts_backend` (preferred) or legacy
    `el_voice_id` for backward compatibility.
    """
    # Resolve the effective external_id: prefer new field, fall back to legacy
    external_id = assignment_request.external_id or assignment_request.el_voice_id
    if not external_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'external_id' or 'el_voice_id' must be provided",
        )

    tts_backend = assignment_request.tts_backend
    # If only el_voice_id was provided (no external_id), force elevenlabs backend
    if not assignment_request.external_id and assignment_request.el_voice_id:
        tts_backend = "elevenlabs"

    try:
        if tts_backend == "elevenlabs":
            # Use the existing ElevenLabs-aware path (verifies voice via EL API)
            voice_service.manual_voice_assignment(professor_id, external_id)
        else:
            # Generic path: look up by backend + external_id in the DB
            voice_service.manual_voice_assignment_generic(
                professor_id, external_id, tts_backend
            )
    except ValueError as e:
        # Use 400 instead of 404 to avoid CloudFront's error response
        # converting it to index.html (CloudFront converts 404/403 to 200+index.html for SPA)
        raise HTTPException(status_code=400, detail=str(e))
    return


@router.get("/", response_model=VoiceListResponse)
async def list_voices(
    gender: Optional[str] = Query(None, description="Filter by gender"),
    accent: Optional[str] = Query(None, description="Filter by accent"),
    age: Optional[str] = Query(None, description="Filter by age"),
    language: Optional[str] = Query(None, description="Filter by language (default: 'en')"),
    use_case: Optional[str] = Query(None, description="Filter by use case"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tts_backend: Optional[str] = Query(None, description="Filter by TTS backend"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    List available voices with optional filtering and pagination.
    """
    voices_data = voice_service.list_available_voices(
        gender=gender,
        accent=accent,
        age=age,
        language=language,
        use_case=use_case,
        category=category,
        limit=limit,
        offset=offset,
        tts_backend=tts_backend,
    )

    total_count = voice_service.count_available_voices(
        gender=gender,
        accent=accent,
        age=age,
        language=language,
        use_case=use_case,
        category=category,
        tts_backend=tts_backend,
    )

    # Calculate pagination values
    page = offset // limit + 1
    pages = ceil(total_count / limit) if total_count > 0 else 1

    return VoiceListResponse(
        items=[VoiceResponse(**voice) for voice in voices_data],
        total=total_count,
        page=page,
        size=limit,
        pages=pages,
    )


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: int = Path(..., description="Database ID of the voice to retrieve"),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    Get a specific voice by its database ID.
    """
    voice = voice_service.get_voice_by_id(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return VoiceResponse(**voice)


@router.get("/by_external/{backend}/{external_id:path}", response_model=VoiceResponse)
async def get_voice_by_external_id(
    backend: str = Path(..., description="TTS backend (e.g., 'elevenlabs', 'mistral')"),
    external_id: str = Path(..., description="Provider-specific voice identifier"),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    Get a voice by its TTS backend and external identifier.

    For ElevenLabs voices this is the el_voice_id. For Mistral voices
    this is the preset name or custom voice ID.
    """
    if backend == "elevenlabs":
        voice = voice_service.get_voice_by_el_id(external_id)
    else:
        voice_obj = voice_service.repository_factory.voice.get_by_external_id(
            backend, external_id
        )
        voice = voice_obj.model_dump() if voice_obj else None

    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    if "id" not in voice or voice.get("id") is None:
        raise HTTPException(status_code=502, detail="Voice fetched but not persisted")
    return VoiceResponse(**voice)


@router.get("/by_el/{el_voice_id}", response_model=VoiceResponse)
async def get_voice_by_elevenlabs_id(
    el_voice_id: str = Path(..., description="ElevenLabs voice_id to retrieve"),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    Get a specific voice by its ElevenLabs voice_id. If not present in DB,
    fetch from ElevenLabs, persist, and return the DB-backed record.

    Legacy endpoint — prefer /by_external/elevenlabs/{external_id}.
    """
    voice = voice_service.get_voice_by_el_id(el_voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    # Ensure response includes DB id
    if "id" not in voice or voice.get("id") is None:
        raise HTTPException(status_code=502, detail="Voice fetched but not persisted")
    return VoiceResponse(**voice)


# ---------------------------------------------------------------------------
# Voice preview (TTS sample generation)
# ---------------------------------------------------------------------------

class VoicePreviewRequest(BaseModel):
    text: Optional[str] = Field(
        None,
        description="Text to synthesize. If omitted a default sample is used.",
    )
    tts_backend: str = Field(
        "mistral",
        description="TTS backend to use for the preview.",
    )
    voice_id: str = Field(
        ...,
        description="Voice identifier (preset name or external ID).",
    )


class VoicePreviewResponse(BaseModel):
    audio_data_uri: str = Field(
        ..., description="Base64-encoded data URI (audio/mpeg)."
    )
    text: str = Field(..., description="The text that was spoken.")


DEFAULT_PREVIEW_TEXT = (
    "Welcome to Artificial University. "
    "Today we'll explore how ideas take shape and transform our understanding of the world."
)


@router.post("/preview", response_model=VoicePreviewResponse, dependencies=[Depends(require_auth)])
async def preview_voice(
    request: VoicePreviewRequest = Body(...),
):
    """
    Generate a short TTS audio sample for a given voice.

    Returns the audio as a base64 data-URI string so the frontend can play
    it directly without storing a file.
    """
    text = request.text or DEFAULT_PREVIEW_TEXT

    try:
        backend: TTSBackend = create_tts_backend(
            backend_name=request.tts_backend,
            logger=logger,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        audio_bytes = backend.text_to_speech(
            text=text,
            voice_id=request.voice_id,
        )
    except Exception as e:
        logger.error("Voice preview generation failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"TTS generation failed: {e}",
        )

    b64 = base64.b64encode(audio_bytes).decode("ascii")
    data_uri = f"data:audio/mpeg;base64,{b64}"

    return VoicePreviewResponse(audio_data_uri=data_uri, text=text)
