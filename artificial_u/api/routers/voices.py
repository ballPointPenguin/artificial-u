"""
API router for voice-related operations.
"""

from math import ceil
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from artificial_u.api.dependencies import get_voice_service
from artificial_u.api.models.voice import (
    ManualVoiceAssignmentRequest,
    VoiceListResponse,
    VoiceResponse,
)
from artificial_u.api.security.auth0 import require_auth
from artificial_u.services.voice_service import VoiceService

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
    """
    try:
        voice_service.manual_voice_assignment(professor_id, assignment_request.el_voice_id)
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
    )

    total_count = voice_service.count_available_voices(
        gender=gender,
        accent=accent,
        age=age,
        language=language,
        use_case=use_case,
        category=category,
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


@router.get("/by_el/{el_voice_id}", response_model=VoiceResponse)
async def get_voice_by_elevenlabs_id(
    el_voice_id: str = Path(..., description="ElevenLabs voice_id to retrieve"),
    voice_service: VoiceService = Depends(get_voice_service),
):
    """
    Get a specific voice by its ElevenLabs voice_id. If not present in DB,
    fetch from ElevenLabs, persist, and return the DB-backed record.
    """
    voice = voice_service.get_voice_by_el_id(el_voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    # Ensure response includes DB id
    if "id" not in voice or voice.get("id") is None:
        raise HTTPException(status_code=502, detail="Voice fetched but not persisted")
    return VoiceResponse(**voice)
