"""
Student router for handling student profile operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from artificial_u.api.dependencies import ensure_student, get_repository_factory
from artificial_u.api.models import StudentResponse, StudentUpdate
from artificial_u.api.security.auth0 import require_auth
from artificial_u.models.repositories.factory import RepositoryFactory

router = APIRouter(
    prefix="/students",
    tags=["students"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/me",
    response_model=StudentResponse,
    summary="Get current student profile",
    description="Get the profile information for the currently authenticated student.",
    dependencies=[Depends(require_auth)],
)
def get_current_student_profile(student=Depends(ensure_student)):
    """
    Get the current authenticated student's profile.

    Returns the student's name, email, and other profile information.
    """
    return StudentResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        auth0_sub=student.auth0_sub,
        role=student.role,
        coins=student.coins,
        is_active=student.is_active,
    )


@router.patch(
    "/me",
    response_model=StudentResponse,
    summary="Update current student profile",
    description="Update the profile information for the currently authenticated student.",
    dependencies=[Depends(require_auth)],
)
def update_current_student_profile(
    update_data: StudentUpdate,
    student=Depends(ensure_student),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Update the current authenticated student's profile.

    Only the fields provided in the request body will be updated.
    """
    # Get the repository
    student_repo = repository_factory.student

    # Prepare update data - only include fields that are set
    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        # No fields to update
        return StudentResponse(
            id=student.id,
            name=student.name,
            email=student.email,
            auth0_sub=student.auth0_sub,
            role=student.role,
            coins=student.coins,
            is_active=student.is_active,
        )

    try:
        # Update the student
        updated_student = student_repo.update_fields(student.id, update_dict)

        if not updated_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        return StudentResponse(
            id=updated_student.id,
            name=updated_student.name,
            email=updated_student.email,
            auth0_sub=updated_student.auth0_sub,
            role=updated_student.role,
            coins=updated_student.coins,
            is_active=updated_student.is_active,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update student profile: {str(e)}",
        )
