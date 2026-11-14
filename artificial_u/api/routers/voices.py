"""
API router for voice-related operations.
"""

import base64
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from artificial_u.api.dependencies import ensure_student, get_repository_factory, get_voice_service
from artificial_u.api.models.voice import (
    ManualVoiceAssignmentRequest,
    VoiceCloneToMistralRequest,
    VoiceDesignPreview,
    VoiceDesignPreviewsResponse,
    VoiceDesignSaveRequest,
    VoiceResponse,
)
from artificial_u.api.security.auth0 import require_auth, verify_asset_ownership
from artificial_u.integrations.mistral.voice_manager import MistralVoiceManager
from artificial_u.integrations.qwen.voice_manager import QwenVoiceManager
from artificial_u.integrations.tts import TTSBackend, create_tts_backend
from artificial_u.integrations.xai.voice_manager import XAIVoiceManager
from artificial_u.models.core import Student
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.voice_service import LOCALIZED_PREVIEW_TEXTS, VoiceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/voices",
    tags=["voices"],
    responses={404: {"description": "Not found"}},
)


# The handlers in this module are plain ``def`` on purpose: they make blocking provider and
# database calls, so FastAPI runs them in its threadpool instead of on the event loop that
# the job worker and SSE streams share.


def _require_professor_access(
    professor_id: int, repository_factory: RepositoryFactory, student: Student
) -> None:
    """Allow only the professor's creator or an admin to change the professor's voice.

    Professors without a recorded creator can only be changed by admins.
    """
    professor = repository_factory.professor.get(professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail=f"Professor with ID {professor_id} not found")
    verify_asset_ownership(student.id, professor.created_by, student.role, "professor")


OWNER_OR_ADMIN = {403: {"description": "Not the professor's creator and not an admin"}}


@router.post("/{professor_id}/assign_voice", status_code=204, responses=OWNER_OR_ADMIN)
def manual_assign_voice(
    professor_id: int = Path(..., description="ID of the professor to assign voice to"),
    assignment_request: ManualVoiceAssignmentRequest = Body(...),
    voice_service: VoiceService = Depends(get_voice_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Manually assign a voice to a professor.

    Accepts either `external_id` + `tts_backend` (preferred) or legacy
    `el_voice_id` for backward compatibility. Only the professor's creator or an
    admin may do this.
    """
    _require_professor_access(professor_id, repository_factory, student)

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
            voice_service.manual_voice_assignment_generic(professor_id, external_id, tts_backend)
    except ValueError as e:
        # The service raises ValueError for an unknown voice and for invalid input alike
        raise HTTPException(status_code=400, detail=str(e))
    return


# ---------------------------------------------------------------------------
# Voice Design (ElevenLabs text-to-voice)
# ---------------------------------------------------------------------------


@router.post(
    "/design/previews",
    response_model=VoiceDesignPreviewsResponse,
    responses=OWNER_OR_ADMIN,
)
def generate_voice_design_previews(
    professor_id: int = Body(..., embed=True),
    language: Optional[str] = Body(None, embed=True),
    voice_service: VoiceService = Depends(get_voice_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """Generate Voice Design audio previews for a professor.

    Builds a voice prompt from the professor's attributes and calls the
    ElevenLabs Voice Design API.  Returns up to 3 short audio previews
    (base64 MP3) along with their temporary ``generated_voice_id`` values.

    The client should present the previews to the user and call
    ``POST /design/save`` with the chosen ``generated_voice_id``.
    """
    _require_professor_access(professor_id, repository_factory, student)

    try:
        previews = voice_service.generate_voice_design_previews(professor_id, language=language)
        return VoiceDesignPreviewsResponse(previews=[VoiceDesignPreview(**p) for p in previews])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Voice Design preview generation failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Voice Design API error: {e}")


@router.post(
    "/design/save",
    response_model=VoiceResponse,
    responses=OWNER_OR_ADMIN,
)
def save_voice_design(
    request: VoiceDesignSaveRequest = Body(...),
    voice_service: VoiceService = Depends(get_voice_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """Save a selected Voice Design preview to the ElevenLabs library.

    Permanently saves the chosen preview as a named voice in the ElevenLabs
    voice library, creates a ``Voice`` record in the database, and assigns
    the voice to the professor.
    """
    _require_professor_access(request.professor_id, repository_factory, student)

    try:
        voice = voice_service.save_designed_voice(
            professor_id=request.professor_id,
            generated_voice_id=request.generated_voice_id,
            voice_name=request.voice_name,
            voice_description=request.voice_description,
        )
        return VoiceResponse(**voice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to save designed voice: %s", e)
        raise HTTPException(status_code=502, detail=f"Failed to save voice: {e}")


@router.post(
    "/clone-to-mistral",
    response_model=VoiceResponse,
    responses=OWNER_OR_ADMIN,
)
def clone_voice_to_mistral(
    request: VoiceCloneToMistralRequest = Body(...),
    voice_service: VoiceService = Depends(get_voice_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """Clone a professor's current ElevenLabs voice into the Mistral voice library.

    Downloads the ElevenLabs voice preview audio and submits it to Mistral as a
    voice clone sample.  The professor is re-associated with the resulting Mistral
    voice; the original ElevenLabs voice record is left intact.
    """
    _require_professor_access(request.professor_id, repository_factory, student)

    try:
        voice = voice_service.clone_elevenlabs_voice_to_mistral(request.professor_id)
        return VoiceResponse(**voice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to clone voice to Mistral: %s", e)
        raise HTTPException(status_code=502, detail=f"Voice cloning failed: {e}")


@router.get("/{voice_id}", response_model=VoiceResponse)
def get_voice(
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


# ---------------------------------------------------------------------------
# Mistral voice catalog (on-demand from Mistral API)
# ---------------------------------------------------------------------------


class MistralVoiceCatalogItem(BaseModel):
    """A voice from the Mistral API, mapped into a shape the frontend can use."""

    id: str = Field(..., description="Mistral voice UUID")
    name: str = Field(..., description="Display name")
    slug: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    languages: Optional[list] = None
    tags: Optional[list] = None


class MistralVoiceCatalogResponse(BaseModel):
    items: list[MistralVoiceCatalogItem]
    total: int


@router.get(
    "/mistral/catalog",
    response_model=MistralVoiceCatalogResponse,
    dependencies=[Depends(require_auth)],
)
def list_mistral_catalog(
    language: Optional[str] = Query(None, description="Filter by language prefix (e.g. 'en')"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
):
    """
    List voices directly from the Mistral Voices API.

    These are **not** stored in our database. The frontend uses the Mistral
    voice ``id`` (UUID) as the ``voice_id`` when previewing or assigning.
    """
    try:
        mgr = MistralVoiceManager()
        raw_voices = mgr.list_voices(limit=100)
    except Exception as e:
        logger.error("Failed to fetch Mistral voice catalog: %s", e)
        raise HTTPException(status_code=502, detail=f"Mistral API error: {e}")

    items: list[MistralVoiceCatalogItem] = []
    for v in raw_voices:
        # Optional client-side filters
        if language:
            langs = v.get("languages") or []
            if not any(str(lang).startswith(language) for lang in langs):
                continue
        if gender and v.get("gender") != gender:
            continue

        items.append(
            MistralVoiceCatalogItem(
                id=v["id"],
                name=v.get("name") or v["id"],
                slug=v.get("slug"),
                gender=v.get("gender"),
                age=v.get("age"),
                languages=v.get("languages"),
                tags=v.get("tags"),
            )
        )

    return MistralVoiceCatalogResponse(items=items, total=len(items))


# ---------------------------------------------------------------------------
# xAI voice catalog (on-demand from the xAI API)
# ---------------------------------------------------------------------------


class XaiVoiceCatalogItem(BaseModel):
    """A voice from the xAI API, mapped into a shape the frontend can use."""

    id: str = Field(..., description="xAI voice id (e.g. 'eve', 'camille')")
    name: str = Field(..., description="Display name")
    language: Optional[str] = None
    gender: Optional[str] = None


class XaiVoiceCatalogResponse(BaseModel):
    items: list[XaiVoiceCatalogItem]
    total: int


@router.get(
    "/xai/catalog",
    response_model=XaiVoiceCatalogResponse,
    dependencies=[Depends(require_auth)],
)
def list_xai_catalog(
    language: Optional[str] = Query(None, description="Filter by language prefix (e.g. 'fr')"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
):
    """
    List voices directly from the xAI Voices API.

    These are **not** stored in our database. The frontend uses the xAI voice
    ``id`` as the ``voice_id`` when previewing or assigning. The catalog is read
    fresh each time so newly added xAI voices appear automatically.
    """
    try:
        mgr = XAIVoiceManager()
        raw_voices = mgr.list_voices()
    except Exception as e:
        logger.error("Failed to fetch xAI voice catalog: %s", e)
        raise HTTPException(status_code=502, detail=f"xAI API error: {e}")

    items: list[XaiVoiceCatalogItem] = []
    for v in raw_voices:
        if not v.get("id"):
            continue
        # Optional client-side filters
        if language:
            lang = v.get("language") or ""
            if not str(lang).startswith(language):
                continue
        if gender and v.get("gender") != gender:
            continue

        items.append(
            XaiVoiceCatalogItem(
                id=v["id"],
                name=v.get("name") or v["id"],
                language=v.get("language"),
                gender=v.get("gender"),
            )
        )

    return XaiVoiceCatalogResponse(items=items, total=len(items))


# ---------------------------------------------------------------------------
# Qwen (Alibaba) voice catalog (static system-voice list)
# ---------------------------------------------------------------------------


class QwenVoiceCatalogItem(BaseModel):
    """A Qwen voice, mapped into a shape the frontend can use."""

    id: str = Field(..., description="Qwen voice id (e.g. 'Brian_v3.1')")
    name: str = Field(..., description="Display name")
    gender: Optional[str] = None
    description: Optional[str] = None
    languages: Optional[list] = None
    model: Optional[str] = Field(None, description="qwen-audio TTS model this voice belongs to")


class QwenVoiceCatalogResponse(BaseModel):
    items: list[QwenVoiceCatalogItem]
    total: int


@router.get(
    "/qwen/catalog",
    response_model=QwenVoiceCatalogResponse,
    dependencies=[Depends(require_auth)],
)
def list_qwen_catalog(
    language: Optional[str] = Query(None, description="Filter by language prefix (e.g. 'en')"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
):
    """
    List the Qwen (Alibaba) voices.

    Alibaba exposes no voice-list API for qwen-audio-3.1-tts-flash, so this
    serves a static catalog of the Singapore-region system voices. These are
    **not** stored in our database; the frontend uses the Qwen voice ``id`` as
    the ``voice_id`` when previewing or assigning.
    """
    raw_voices = QwenVoiceManager().list_voices()

    items: list[QwenVoiceCatalogItem] = []
    for v in raw_voices:
        # Optional client-side filters
        if language:
            langs = v.get("languages") or []
            if not any(str(lang).startswith(language) for lang in langs):
                continue
        if gender and v.get("gender") != gender:
            continue

        items.append(
            QwenVoiceCatalogItem(
                id=v["id"],
                name=v.get("name") or v["id"],
                gender=v.get("gender"),
                description=v.get("description"),
                languages=v.get("languages"),
                model=v.get("model"),
            )
        )

    return QwenVoiceCatalogResponse(items=items, total=len(items))


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
    language: Optional[str] = Field(
        None,
        description="Optional language prefix of the user ('en', 'fr', 'es', 'zh').",
    )
    professor_id: Optional[int] = Field(
        None,
        description=(
            "Professor the voice is being auditioned for. The caller must be that "
            "professor's creator or an admin; without it the preview is admin-only."
        ),
    )


class VoicePreviewResponse(BaseModel):
    audio_data_uri: str = Field(..., description="Base64-encoded data URI (audio/mpeg).")
    text: str = Field(..., description="The text that was spoken.")


@router.post("/preview", response_model=VoicePreviewResponse, responses=OWNER_OR_ADMIN)
def preview_voice(
    request: VoicePreviewRequest = Body(...),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Generate a short TTS audio sample for a given voice.

    Returns the audio as a base64 data-URI string so the frontend can play
    it directly without storing a file. Each preview is a paid provider call, so it
    is limited to the creator of the professor being worked on, or an admin.
    """
    if request.professor_id is not None:
        _require_professor_access(request.professor_id, repository_factory, student)
    elif student.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Voice previews that are not for a specific professor are limited to admins.",
        )

    if request.text:
        text = request.text
    else:
        lang = request.language or "en"
        text = LOCALIZED_PREVIEW_TEXTS.get(lang.lower()[:2], LOCALIZED_PREVIEW_TEXTS["en"])

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
