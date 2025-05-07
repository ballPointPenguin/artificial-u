"""
Topic API service for handling topic operations in the API layer.
"""

import logging
from typing import List, Optional

from fastapi import HTTPException, status

from artificial_u.api.models.topics import (
    Topic,
    TopicCreate,
    TopicList,
    TopicsGenerate,
    TopicUpdate,
)
from artificial_u.models.core import Topic as CoreTopic
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import TopicService as CoreTopicService
from artificial_u.utils import (
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
    TopicNotFoundError,
)


class TopicApiService:
    """Service for handling topic API operations."""

    def __init__(
        self,
        core_topic_service: CoreTopicService,
        repository_factory: RepositoryFactory,  # For potential direct use, e.g. counts if added
        logger: Optional[logging.Logger] = None,
    ):
        self.core_topic_service = core_topic_service
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    def get_topic(self, topic_id: int) -> Topic:
        """Get a topic by its ID."""
        try:
            core_topic = self.core_topic_service.get_topic(topic_id)
            if not core_topic:
                raise TopicNotFoundError(f"Topic with ID {topic_id} not found")
            return Topic.model_validate(core_topic)
        except TopicNotFoundError as e:
            self.logger.warning(f"Topic not found: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except DatabaseError as e:
            self.logger.error(f"Database error getting topic {topic_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
            )

    def list_topics_by_course(self, course_id: int, page: int = 1, size: int = 10) -> TopicList:
        """List topics for a course with pagination."""
        try:
            # Core service currently returns all topics for the course
            all_core_topics = self.core_topic_service.list_topics_by_course(course_id)

            total_count = len(all_core_topics)
            start = (page - 1) * size
            end = start + size
            paginated_core_topics = all_core_topics[start:end]

            topic_items = [Topic.model_validate(topic) for topic in paginated_core_topics]

            return TopicList(
                items=topic_items,
                total=total_count,
                page=page,
                page_size=size,
            )
        except CourseNotFoundError as e:
            self.logger.warning(f"Course not found for listing topics: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except DatabaseError as e:
            self.logger.error(
                f"Database error listing topics for course {course_id}: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
            )

    def create_topic(self, topic_data: TopicCreate) -> Topic:
        """Create a new topic."""
        try:
            core_topic = self.core_topic_service.create_topic(
                title=topic_data.title,
                course_id=topic_data.course_id,
                week=topic_data.week,
                order=topic_data.order,
            )
            return Topic.model_validate(core_topic)
        except DatabaseError as e:
            self.logger.error(f"Database error creating topic: {e}", exc_info=True)
            # Could be a 400 or 409 depending on the nature of DB error
            # (e.g., FK constraint for course_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Database error: {e}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error creating topic: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
            )

    def update_topic(self, topic_id: int, topic_data: TopicUpdate) -> Topic:
        """Update an existing topic."""
        try:
            # Get existing core topic to update
            core_topic_to_update = self.core_topic_service.get_topic(topic_id)
            if not core_topic_to_update:
                raise TopicNotFoundError(f"Topic with ID {topic_id} not found for update.")

            # Create a new CoreTopic instance with updated fields
            update_payload = topic_data.model_dump(exclude_unset=True)

            updated_core_topic = CoreTopic(
                id=topic_id,  # Keep the original ID
                title=update_payload.get("title", core_topic_to_update.title),
                course_id=update_payload.get("course_id", core_topic_to_update.course_id),
                week=update_payload.get("week", core_topic_to_update.week),
                order=update_payload.get("order", core_topic_to_update.order),
            )

            # Call core service update method
            persisted_topic = self.core_topic_service.update_topic(updated_core_topic)
            return Topic.model_validate(persisted_topic)
        except TopicNotFoundError as e:
            self.logger.warning(f"Topic not found for update: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except DatabaseError as e:
            self.logger.error(f"Database error updating topic {topic_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Database error: {e}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error updating topic {topic_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
            )

    def delete_topic(self, topic_id: int) -> bool:
        """Delete a topic."""
        try:
            deleted = self.core_topic_service.delete_topic(topic_id)
            if not deleted:
                # Core service delete_topic returns False if not found,
                # but doesn't raise TopicNotFound.
                # We ensure 404 if not deleted.
                error_detail = (
                    f"Topic with ID {topic_id} not found for deletion or operation failed."
                )
                raise TopicNotFoundError(error_detail)
            return True
        except TopicNotFoundError as e:
            self.logger.warning(f"Topic not found for deletion: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except DatabaseError as e:
            self.logger.error(f"Database error deleting topic {topic_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error deleting topic {topic_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
            )

    async def generate_topics_for_course(self, generation_data: TopicsGenerate) -> List[Topic]:
        """Generate topics for a course using the core service."""
        try:
            self.logger.info(
                f"API Service: Generating topics for course ID: {generation_data.course_id}"
            )
            core_topics = await self.core_topic_service.generate_topics_for_course(
                course_id=generation_data.course_id,
                freeform_prompt=generation_data.freeform_prompt,
            )
            return [Topic.model_validate(topic) for topic in core_topics]
        except CourseNotFoundError as e:
            self.logger.warning(f"Course not found for topic generation: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ContentGenerationError as e:
            self.logger.error(f"Content generation error for topics: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Content generation error: {str(e)[:500]}",  # Truncate long messages
            )
        except DatabaseError as e:
            self.logger.error(f"Database error during topic generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)[:500]}",  # Truncate long messages
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during topic generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
            )
