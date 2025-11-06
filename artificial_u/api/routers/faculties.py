"""
Faculty router for handling faculty-related API endpoints.
"""

from fastapi import APIRouter, Depends

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
    faculty_service: FacultyApiService = Depends(get_faculty_api_service),
):
    """
    Get a list of all faculties.

    Returns:
        List of all faculties
    """
    return faculty_service.list_faculties()
