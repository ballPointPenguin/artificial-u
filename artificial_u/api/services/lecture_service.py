"""
Lecture API service for handling lecture operations in the API layer.
"""

import hashlib
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from artificial_u.api.config import get_settings
from artificial_u.api.models.lectures import (
    Lecture,
    LectureCreate,
    LectureList,
    LectureUpdate,
)
from artificial_u.models.core import Lecture as LectureCore
from artificial_u.models.database import Repository
from artificial_u.utils.exceptions import LectureNotFoundError


# Add content_asset_field to track content files in DB
class LectureApiService:
    """Service for handling lecture API operations."""

    def __init__(self, repository: Repository, storage_service=None):
        """Initialize the lecture service with a repository and optional storage service."""
        self.repository = repository
        self.storage_service = storage_service
        self.settings = get_settings()

    def get_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> LectureList:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            search_query: Search query for title/description

        Returns:
            LectureList: Paginated list of lectures
        """
        # Get lectures from repository with filtering
        lectures = self.repository.list_lectures(
            page=page,
            size=size,
            course_id=course_id,
            professor_id=professor_id,
            search_query=search_query,
        )

        total_count = self.repository.count_lectures(
            course_id=course_id,
            professor_id=professor_id,
            search_query=search_query,
        )

        # Convert core models to API models
        lecture_items = []
        for lecture in lectures:
            if isinstance(lecture, str):
                continue  # Skip invalid string items
            if (
                isinstance(lecture, dict)
                and all(
                    key in lecture
                    for key in [
                        "id",
                        "title",
                        "description",
                        "content",
                        "course_id",
                        "week_number",
                        "order_in_week",
                        "audio_url",
                        "generated_at",
                    ]
                )
                or (
                    hasattr(lecture, "id")
                    and hasattr(lecture, "title")
                    and hasattr(lecture, "description")
                    and hasattr(lecture, "content")
                    and hasattr(lecture, "course_id")
                    and hasattr(lecture, "week_number")
                    and hasattr(lecture, "order_in_week")
                    and hasattr(lecture, "audio_url")
                    and hasattr(lecture, "generated_at")
                )
            ):
                lecture_items.append(
                    Lecture(
                        id=lecture.id,
                        title=lecture.title,
                        description=lecture.description,
                        content=lecture.content,
                        course_id=lecture.course_id,
                        week_number=lecture.week_number,
                        order_in_week=lecture.order_in_week,
                        audio_url=lecture.audio_url,
                        generated_at=lecture.generated_at,
                    )
                )
            else:
                continue  # Skip invalid items

        return LectureList(
            items=lecture_items,
            total=total_count,
            page=page,
            page_size=size,
        )

    def get_lecture(self, lecture_id: int) -> Optional[Lecture]:
        """
        Get detailed information about a specific lecture.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Lecture: Lecture information or None if not found
        """
        lecture = self.repository.get_lecture(lecture_id)
        if not lecture:
            return None

        # audio_url is now directly from the model
        return Lecture(
            id=lecture.id,
            title=lecture.title,
            description=lecture.description,
            content=lecture.content,
            course_id=lecture.course_id,
            week_number=lecture.week_number,
            order_in_week=lecture.order_in_week,
            audio_url=lecture.audio_url,
            generated_at=lecture.generated_at,
        )

    def get_lecture_content(self, lecture_id: int) -> Optional[Lecture]:
        """
        Get the content of a specific lecture.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Lecture: Lecture with content or None if not found
        """
        # Use the get_lecture method since we're returning the full lecture now
        return self.get_lecture(lecture_id)

    def get_lecture_content_asset_path(self, lecture_id: int) -> Optional[str]:
        """
        Get or generate a file path for the lecture content asset.

        This method implements the lazy asset generation pattern - if the
        content file doesn't exist yet, it will generate a path where it
        should be created.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Optional[str]: Path where content asset exists or should be created
        """
        lecture = self.repository.get_lecture(lecture_id)
        if not lecture:
            return None

        # Generate a predictable path based on lecture details
        # Format: lectures/{course_id}/w{week}_l{order}_{lecture_id}.txt
        course_id = lecture.course_id
        week = lecture.week_number
        order = lecture.order_in_week

        # Create directory if it doesn't exist
        content_dir = os.path.join("assets", "lectures", str(course_id))
        os.makedirs(content_dir, exist_ok=True)

        # Generate filename
        filename = f"w{week}_l{order}_{lecture_id}.txt"
        asset_path = os.path.join(content_dir, filename)

        return asset_path

    async def ensure_content_asset_exists(self, lecture_id: int) -> Optional[str]:
        """
        Ensure a content asset file exists for the lecture.

        If the file doesn't exist, it will be created from the database content.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Optional[str]: Path to the content asset file or None if lecture not found
        """
        lecture = self.repository.get_lecture(lecture_id)
        if not lecture:
            return None

        asset_path = self.get_lecture_content_asset_path(lecture_id)

        # Check if file already exists
        if not os.path.exists(asset_path):
            # Create the file from DB content
            with open(asset_path, "w", encoding="utf-8") as f:
                f.write(lecture.content)

        return asset_path

    async def generate_content_hash(self, lecture_id: int) -> Optional[str]:
        """
        Generate a hash of the lecture content for versioning purposes.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Optional[str]: MD5 hash of the lecture content or None if not found
        """
        lecture = self.repository.get_lecture(lecture_id)
        if not lecture or not lecture.content:
            return None

        # Generate MD5 hash of content for versioning
        content_hash = hashlib.md5(lecture.content.encode("utf-8")).hexdigest()
        return content_hash

    def get_lecture_audio_url(self, lecture_id: int) -> Optional[str]:
        """
        Get the audio file path or URL for a specific lecture.

        This can return either:
        1. A storage URL (e.g., https://storage.example.com/bucket/path/to/file.mp3)
        2. A local file path for backward compatibility (to be deprecated)

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Optional[str]: Path or URL to the audio file, or None if not found/no audio
        """
        # Get the audio url from the repository
        return self.repository.get_lecture_audio_url(lecture_id)

    def create_lecture(self, lecture_data: LectureCreate) -> Lecture:
        """
        Create a new lecture.

        Args:
            lecture_data: The lecture data to create

        Returns:
            Lecture: The created lecture

        Raises:
            HTTPException: If course doesn't exist or other validation errors
        """
        # Validate course exists
        course = self.repository.get_course(lecture_data.course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {lecture_data.course_id} not found",
            )

        # Create core model from API model
        core_lecture = LectureCore(
            title=lecture_data.title,
            course_id=lecture_data.course_id,
            week_number=lecture_data.week_number,
            order_in_week=lecture_data.order_in_week,
            description=lecture_data.description,
            content=lecture_data.content,
            audio_url=lecture_data.audio_url,
        )

        try:
            # Save to database
            lecture = self.repository.create_lecture(core_lecture)

            # Return the created lecture
            return self.get_lecture(lecture.id)
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create lecture: {str(e)}",
            )

    def update_lecture(
        self, lecture_id: int, lecture_data: LectureUpdate
    ) -> Optional[Lecture]:
        """
        Update an existing lecture.

        Args:
            lecture_id: The unique identifier of the lecture to update
            lecture_data: The updated lecture data

        Returns:
            Optional[Lecture]: The updated lecture or None if not found
        """
        # Get existing lecture
        lecture = self.repository.get_lecture(lecture_id)
        if not lecture:
            return None

        # Update fields that are present in the update data
        if lecture_data.title is not None:
            lecture.title = lecture_data.title

        if lecture_data.description is not None:
            lecture.description = lecture_data.description

        if lecture_data.content is not None:
            lecture.content = lecture_data.content

            # If content was updated, we should remove any existing content asset
            # so it will be regenerated with new content when requested
            asset_path = self.get_lecture_content_asset_path(lecture_id)
            if os.path.exists(asset_path):
                try:
                    os.remove(asset_path)
                except (OSError, PermissionError) as e:
                    # Log error but don't fail the update
                    print(f"Warning: Failed to remove outdated content asset: {str(e)}")

        if lecture_data.week_number is not None:
            lecture.week_number = lecture_data.week_number

        if lecture_data.order_in_week is not None:
            lecture.order_in_week = lecture_data.order_in_week

        if lecture_data.audio_url is not None:
            lecture.audio_url = lecture_data.audio_url

        # Save updated lecture
        updated_lecture = self.repository.update_lecture(lecture)

        # Return updated lecture with details
        return self.get_lecture(updated_lecture.id)

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: The unique identifier of the lecture to delete

        Returns:
            bool: True if lecture was deleted, False if not found
        """
        # Simply delete the lecture database record and let assets remain
        return self.repository.delete_lecture(lecture_id)
