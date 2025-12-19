"""
Preferences router for handling global and user preferences.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from artificial_u.api.dependencies import ensure_student, get_repository_factory
from artificial_u.api.security.auth0 import require_auth, require_role
from artificial_u.models.core import Preference, PreferenceCreate
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.preference_service import PreferenceService

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    responses={404: {"description": "Not found"}},
)


class PreferenceResponse(BaseModel):
    """Response model for a preference."""

    id: int
    student_id: Optional[int] = None
    scope: str
    value: str
    is_global: bool


class PreferenceValueUpdate(BaseModel):
    """Request model for updating a preference value."""

    value: str = Field(..., description="The new preference value")


class LectureModelResponse(BaseModel):
    """Response model for lecture generation model."""

    model: str = Field(..., description="The current lecture generation model")
    source: str = Field(
        ..., description="Source of the model setting (preference or environment)"
    )


@router.get(
    "/global",
    response_model=List[PreferenceResponse],
    summary="List all global preferences",
    description="Get all global application preferences. Admin only.",
    dependencies=[Depends(require_role("admin"))],
)
def list_global_preferences(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    List all global preferences.

    Requires admin role.
    """
    prefs = repository_factory.preference.list_all(is_global=True)
    return [
        PreferenceResponse(
            id=pref.id,
            student_id=pref.student_id,
            scope=pref.scope,
            value=pref.value,
            is_global=pref.is_global,
        )
        for pref in prefs
    ]


@router.get(
    "/global/{scope}",
    response_model=PreferenceResponse,
    summary="Get a global preference",
    description="Get a specific global preference by scope. Admin only.",
    dependencies=[Depends(require_role("admin"))],
)
def get_global_preference(
    scope: str = Path(..., description="The preference scope/key"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Get a global preference by scope.

    Requires admin role.
    """
    pref = repository_factory.preference.get_global(scope)
    if not pref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Global preference '{scope}' not found",
        )

    return PreferenceResponse(
        id=pref.id,
        student_id=pref.student_id,
        scope=pref.scope,
        value=pref.value,
        is_global=pref.is_global,
    )


@router.put(
    "/global/{scope}",
    response_model=PreferenceResponse,
    summary="Set a global preference",
    description="Create or update a global preference. Admin only.",
    dependencies=[Depends(require_role("admin"))],
)
def set_global_preference(
    update_data: PreferenceValueUpdate,
    scope: str = Path(..., description="The preference scope/key"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Set or update a global preference.

    Requires admin role.
    """
    try:
        pref = repository_factory.preference.set_global(scope, update_data.value)
        return PreferenceResponse(
            id=pref.id,
            student_id=pref.student_id,
            scope=pref.scope,
            value=pref.value,
            is_global=pref.is_global,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set preference: {str(e)}",
        )


@router.delete(
    "/global/{scope}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a global preference",
    description="Delete a global preference by scope. Admin only.",
    dependencies=[Depends(require_role("admin"))],
)
def delete_global_preference(
    scope: str = Path(..., description="The preference scope/key"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Delete a global preference.

    Requires admin role.
    """
    deleted = repository_factory.preference.delete_by_scope(scope, student_id=None)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Global preference '{scope}' not found",
        )


@router.get(
    "/models/lecture-generation",
    response_model=LectureModelResponse,
    summary="Get lecture generation model",
    description="Get the currently configured lecture generation model.",
    dependencies=[Depends(require_auth)],
)
def get_lecture_generation_model(
    student=Depends(ensure_student),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Get the lecture generation model setting.

    Returns the model name and the source (preference or environment).
    """
    pref_service = PreferenceService(repository_factory)
    model = pref_service.get_lecture_generation_model(student_id=student.id)

    # Check if it came from preferences or environment
    pref = repository_factory.preference.get(student.id, PreferenceService.LECTURE_GENERATION_MODEL)
    source = "preference" if pref else "environment"

    return LectureModelResponse(model=model, source=source)
