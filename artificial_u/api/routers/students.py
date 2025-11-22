"""
Student router for handling student profile operations.
"""

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from artificial_u.api.dependencies import ensure_student, get_repository_factory
from artificial_u.api.models import (
    StudentCoinsAdd,
    StudentResponse,
    StudentRoleUpdate,
    StudentsListResponse,
    StudentUpdate,
)
from artificial_u.api.security.auth0 import require_auth, require_role
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


@router.get(
    "",
    response_model=StudentsListResponse,
    summary="List all students (Admin only)",
    description="Get a paginated list of all students. Requires admin role.",
    dependencies=[require_role("admin")],
)
def list_students(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    email: Optional[str] = Query(None, description="Filter by email (partial match)"),
    role: Optional[str] = Query(None, description="Filter by role (viewer, creator, admin)"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Get a paginated list of students with optional filtering.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **name**: Filter by student name (partial match)
    - **email**: Filter by email (partial match)
    - **role**: Filter by role (exact match)
    """
    student_repo = repository_factory.student

    # Get all students
    all_students = student_repo.list_all()

    # Apply filters
    filtered_students = all_students
    if name:
        filtered_students = [s for s in filtered_students if name.lower() in s.name.lower()]
    if email:
        filtered_students = [
            s for s in filtered_students if s.email and email.lower() in s.email.lower()
        ]
    if role:
        filtered_students = [s for s in filtered_students if s.role == role]

    # Calculate pagination
    total = len(filtered_students)
    pages = ceil(total / size) if total > 0 else 1

    # Apply pagination
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_students = filtered_students[start_idx:end_idx]

    # Convert to response models
    items = [
        StudentResponse(
            id=student.id,
            name=student.name,
            email=student.email,
            auth0_sub=student.auth0_sub,
            role=student.role,
            coins=student.coins,
            is_active=student.is_active,
        )
        for student in paginated_students
    ]

    return StudentsListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch(
    "/{student_id}/role",
    response_model=StudentResponse,
    summary="Update student role (Admin only)",
    description="Update a student's role. Requires admin role.",
    dependencies=[require_role("admin")],
)
def update_student_role(
    student_id: int = Path(..., description="ID of the student to update"),
    role_data: StudentRoleUpdate = ...,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Update a student's role.

    - **student_id**: The ID of the student to update
    - **role**: New role (viewer, creator, admin)
    """
    student_repo = repository_factory.student

    try:
        updated_student = student_repo.update_role(student_id, role_data.role)

        return StudentResponse(
            id=updated_student.id,
            name=updated_student.name,
            email=updated_student.email,
            auth0_sub=updated_student.auth0_sub,
            role=updated_student.role,
            coins=updated_student.coins,
            is_active=updated_student.is_active,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update student role: {str(e)}",
        )


@router.post(
    "/{student_id}/coins",
    response_model=StudentResponse,
    summary="Adjust coins for student (Admin only)",
    description=(
        "Adjust a student's coin balance. Positive values add coins and negative values remove coins. "
        "Requires admin role."
    ),
    dependencies=[require_role("admin")],
)
def add_student_coins(
    student_id: int = Path(..., description="ID of the student"),
    coins_data: StudentCoinsAdd = ...,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Adjust a student's coin balance (positive to add, negative to remove).

    - **student_id**: The ID of the student
    - **amount**: Coin adjustment amount (positive to add, negative to remove)
    """
    student_repo = repository_factory.student

    try:
        updated_student = student_repo.add_coins(student_id, coins_data.amount)

        return StudentResponse(
            id=updated_student.id,
            name=updated_student.name,
            email=updated_student.email,
            auth0_sub=updated_student.auth0_sub,
            role=updated_student.role,
            coins=updated_student.coins,
            is_active=updated_student.is_active,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add coins: {str(e)}",
        )


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student (Admin only)",
    description=(
        "Delete a student's account without touching any content they previously created. "
        "Requires admin role."
    ),
    dependencies=[require_role("admin")],
)
def delete_student(
    student_id: int = Path(..., description="ID of the student to delete"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Permanently remove a student's account while leaving their authored resources intact.
    """
    student_repo = repository_factory.student

    try:
        student_repo.delete(student_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete student: {str(e)}",
        )
