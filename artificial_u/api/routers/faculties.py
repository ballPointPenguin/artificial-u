"""
Faculty router for handling faculty-related API endpoints.
"""

from fastapi import APIRouter, Depends, Query

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.models.faculties import FacultiesListResponse
from artificial_u.api.services.faculty_service import FacultyApiService
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(
    prefix="/faculties",
    tags=["faculties"],
    responses={404: {"description": "Not found"}},
)


def get_faculty_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
) -> FacultyApiService:
    """
    Get a faculty API service instance.

    Args:
        repository_factory: Repository factory

    Returns:
        FacultyApiService instance
    """
    import logging

    return FacultyApiService(
        repository_factory=repository_factory,
        logger=logging.getLogger("artificial_u.api.services.faculty_service"),
    )


@router.get(
    "",
    response_model=FacultiesListResponse,
    summary="List faculties",
    description="Get a list of all faculties.",
)
async def list_faculties(
    language: str = Query("en", description="Content language sandbox (e.g., 'en', 'fr')"),
    faculty_service: FacultyApiService = Depends(get_faculty_api_service),
):
    """
    Get a list of faculties for the given language sandbox.

    Returns:
        List of faculties for the requested language
    """
    return faculty_service.list_faculties(language=language)
