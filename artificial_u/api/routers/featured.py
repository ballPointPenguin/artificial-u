"""
Featured items endpoints.

Public endpoints return featured lectures/professors/departments for the homepage.
Admin endpoints allow managing the featured selections.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.security.auth0 import require_role
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(prefix="/featured", tags=["Featured"])

VALID_ITEM_TYPES = {"lecture", "professor", "department"}


# --- Response / Request Models --- #


class FeaturedItemResponse(BaseModel):
    """A featured item record."""

    id: int
    item_type: str
    item_id: int
    language: str
    display_order: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class FeaturedItemCreate(BaseModel):
    """Request body for adding a featured item."""

    item_type: str = Field(..., description="One of: lecture, professor, department")
    item_id: int = Field(..., description="ID of the item in its source table")
    language: str = Field(default="en", description="Language code")
    display_order: int = Field(default=0, description="Sort order (lower = first)")


class FeaturedItemOrderUpdate(BaseModel):
    """Request body for updating display order."""

    display_order: int = Field(..., description="New sort order")


# --- Public Endpoints --- #


@router.get(
    "",
    response_model=List[FeaturedItemResponse],
    summary="List all featured items",
    description="Get all featured items for a language, grouped by type.",
)
async def list_featured(
    language: str = Query("en", description="Language code"),
    item_type: Optional[str] = Query(None, description="Filter by type"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """List featured items. Optionally filter by item_type."""
    if item_type:
        if item_type not in VALID_ITEM_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid item_type. Must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}",
            )
        items = repository_factory.featured.list_by_type(item_type, language=language)
    else:
        items = repository_factory.featured.list_all(language=language)

    return [_to_response(item) for item in items]


# --- Admin Endpoints --- #


@router.post(
    "",
    response_model=FeaturedItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a featured item (Admin only)",
    dependencies=[require_role("admin")],
)
async def add_featured(
    data: FeaturedItemCreate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """Add an item to the featured set. Idempotent -- returns existing if already featured."""
    if data.item_type not in VALID_ITEM_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid item_type. Must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}",
        )

    # Validate that the referenced item exists
    _validate_item_exists(data.item_type, data.item_id, repository_factory)

    item = repository_factory.featured.add(
        item_type=data.item_type,
        item_id=data.item_id,
        language=data.language,
        display_order=data.display_order,
    )
    return _to_response(item)


@router.put(
    "/{featured_id}/order",
    response_model=FeaturedItemResponse,
    summary="Update featured item order (PUT) (Admin only)",
    dependencies=[require_role("admin")],
)
@router.patch(
    "/{featured_id}/order",
    response_model=FeaturedItemResponse,
    summary="Update featured item order (Admin only)",
    dependencies=[require_role("admin")],
)
async def update_featured_order(
    data: FeaturedItemOrderUpdate,
    featured_id: int = Path(..., description="Featured item ID"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """Update the display order of a featured item."""
    updated = repository_factory.featured.update_order(featured_id, data.display_order)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Featured item not found",
        )
    return _to_response(updated)


@router.delete(
    "/{featured_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a featured item (Admin only)",
    dependencies=[require_role("admin")],
)
async def remove_featured(
    featured_id: int = Path(..., description="Featured item ID"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """Remove an item from the featured set."""
    deleted = repository_factory.featured.remove(featured_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Featured item not found",
        )


# --- Helpers --- #


def _validate_item_exists(
    item_type: str,
    item_id: int,
    repository_factory: RepositoryFactory,
) -> None:
    """Raise 404 if the referenced item doesn't exist."""
    if item_type == "lecture":
        if not repository_factory.lecture.get(item_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture {item_id} not found",
            )
    elif item_type == "professor":
        if not repository_factory.professor.get(item_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor {item_id} not found",
            )
    elif item_type == "department":
        if not repository_factory.department.get(item_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {item_id} not found",
            )


def _to_response(item) -> FeaturedItemResponse:
    return FeaturedItemResponse(
        id=item.id,
        item_type=item.item_type,
        item_id=item.item_id,
        language=item.language,
        display_order=item.display_order,
        created_at=item.created_at.isoformat() if item.created_at else None,
    )
