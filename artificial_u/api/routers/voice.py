"""
API router for voice-related operations.
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from artificial_u.api.dependencies import get_voice_service
from artificial_u.api.models.voice import (
    ManualVoiceAssignmentRequest,
    PaginatedVoiceResponse,
    VoiceResponse,
)
from artificial_u.services.voice_service import VoiceService

router = APIRouter(
    prefix="/voices",
    tags=["voices"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{professor_id}/assign_voice", status_code=204)
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
        raise HTTPException(status_code=404, detail=str(e))
    return


@router.get("/", response_model=PaginatedVoiceResponse)
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

    return PaginatedVoiceResponse(
        items=[VoiceResponse(**voice) for voice in voices_data],
        total=total_count,
        limit=limit,
        offset=offset,
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
