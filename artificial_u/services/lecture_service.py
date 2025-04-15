"""
Lecture management service for ArtificialU.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.config.defaults import DEFAULT_LECTURE_WORD_COUNT
from artificial_u.models.core import Course, Lecture, Professor
from artificial_u.services.storage_service import StorageService
from artificial_u.utils.exceptions import (
    ContentGenerationError,
    DatabaseError,
    LectureNotFoundError,
)
from artificial_u.utils.random_generators import RandomGenerators


class LectureService:
    """Service for managing lecture entities."""

    def __init__(
        self,
        repository,
        content_generator,
        professor_service,
        course_service,
        audio_processor=None,
        text_export_path=None,
        content_backend=None,
        content_model=None,
        enable_caching=False,
        storage_service=None,
        logger=None,
    ):
        """
        Initialize the lecture service.

        Args:
            repository: Data repository
            content_generator: Content generation service
            professor_service: Professor management service
            course_service: Course management service
            audio_processor: Optional audio processing service
            text_export_path: Directory for exporting lecture text
            content_backend: Name of content backend being used
            content_model: Name of content model being used
            enable_caching: Whether caching is enabled
            storage_service: Optional storage service for file operations
            logger: Optional logger instance
        """
        self.repository = repository
        self.content_generator = content_generator
        self.professor_service = professor_service
        self.course_service = course_service
        self.audio_processor = audio_processor
        self.text_export_path = text_export_path
        self.content_backend = content_backend
        self.content_model = content_model
        self.enable_caching = enable_caching
        self.storage_service = storage_service or StorageService(logger=logger)
        self.logger = logger or logging.getLogger(__name__)

        # Ensure text export directory exists
        if self.text_export_path:
            Path(self.text_export_path).mkdir(parents=True, exist_ok=True)

    def generate_lecture(
        self,
        course_code: str,
        week: int,
        number: int = 1,
        topic: Optional[str] = None,
        word_count: int = DEFAULT_LECTURE_WORD_COUNT,
    ) -> Tuple[Lecture, Course, Professor]:
        """
        Generate a lecture for a specific course and week.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week
            topic: Lecture topic (if None, will be derived from syllabus)
            word_count: Word count for the lecture

        Returns:
            Tuple: (Lecture, Course, Professor) - The generated lecture with its course and professor
        """
        self.logger.info(
            f"Generating lecture for course {course_code}, week {week}, number {number}"
        )

        # Get course and professor
        course = self.course_service.get_course_by_code(course_code)
        professor = self.professor_service.get_professor(course.professor_id)

        # Get previous lecture for continuity if available
        previous_lecture = self._get_previous_lecture(course, week, number)

        # Determine topic
        lecture_topic = topic or RandomGenerators.generate_lecture_topic(week, number)
        self.logger.debug(f"Using topic: {lecture_topic}")

        # Generate lecture content
        lecture = self._create_lecture_content(
            course, professor, lecture_topic, week, number, previous_lecture, word_count
        )

        # Save lecture to database
        try:
            lecture = self.repository.lecture.create(lecture)
            self.logger.info(f"Lecture created with ID: {lecture.id}")
        except Exception as e:
            error_msg = f"Failed to save lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

        # Export lecture text to file if export path is configured
        if self.text_export_path:
            # Handle exporting lecture text
            import asyncio

            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                # Check if we're in an async context
                if loop.is_running():
                    # We're in an async context (e.g., in a test with pytest-asyncio)
                    # Schedule the task without waiting for it
                    asyncio.create_task(
                        self.export_lecture_text(lecture, course, professor)
                    )
                else:
                    # We're not in an async context, run the coroutine to completion
                    loop.run_until_complete(
                        self.export_lecture_text(lecture, course, professor)
                    )
            except RuntimeError:
                # No event loop in this thread, create a new one
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(
                        self.export_lecture_text(lecture, course, professor)
                    )
                finally:
                    loop.close()

        return lecture, course, professor

    def _get_previous_lecture(
        self, course: Course, week: int, number: int
    ) -> Optional[Lecture]:
        """
        Get previous lecture for continuity if available.

        Args:
            course: Course object
            week: Current week number
            number: Current lecture number

        Returns:
            Optional[Lecture]: Previous lecture if available, None otherwise
        """
        if week <= 1 and number <= 1:
            return None

        prev_week = week
        prev_number = number - 1

        if prev_number < 1:
            prev_week -= 1
            prev_number = course.lectures_per_week

        try:
            previous_lecture = self.repository.lecture.get_by_course_week_order(
                course_id=course.id, week_number=prev_week, order_in_week=prev_number
            )
            if previous_lecture:
                self.logger.debug(
                    f"Found previous lecture from week {prev_week}, number {prev_number}"
                )
            return previous_lecture
        except Exception as e:
            self.logger.warning(
                f"Failed to retrieve previous lecture: {str(e)}. Continuing without previous content."
            )
            return None

    def _create_lecture_content(
        self,
        course: Course,
        professor: Professor,
        topic: str,
        week_number: int,
        order_in_week: int,
        previous_lecture: Optional[Lecture] = None,
        word_count: int = DEFAULT_LECTURE_WORD_COUNT,
    ) -> Lecture:
        """
        Generate lecture content using the content generator.

        Args:
            course: Course object
            professor: Professor object
            topic: Lecture topic
            week_number: Week number in the course
            order_in_week: Order of this lecture within the week
            previous_lecture: Optional previous lecture for continuity
            word_count: Target word count for the lecture

        Returns:
            Lecture: Generated lecture object

        Raises:
            ContentGenerationError: If lecture generation fails
        """
        previous_content = previous_lecture.content if previous_lecture else None

        try:
            # Use cached lecture generation if enabled for Anthropic
            if self.enable_caching and self.content_backend == "anthropic":
                self.logger.info(
                    f"Generating lecture for {course.code} Week {week_number}, Lecture {order_in_week} with caching"
                )
                lecture, cache_metrics = (
                    self.content_generator.create_lecture_with_caching(
                        course=course,
                        professor=professor,
                        topic=topic,
                        week_number=week_number,
                        order_in_week=order_in_week,
                        previous_lecture_content=previous_content,
                        word_count=word_count,
                    )
                )

                # Log cache metrics
                if cache_metrics.get("cached", False):
                    self.logger.info(
                        f"Cache metrics - Tokens saved: {cache_metrics.get('estimated_tokens_saved', 0)}, "
                        f"Response time: {cache_metrics.get('response_time_seconds', 0):.2f}s"
                    )
            else:
                # Use standard generation without caching
                self.logger.info(
                    f"Generating lecture for {course.code} Week {week_number}, Lecture {order_in_week}"
                )
                lecture = self.content_generator.create_lecture(
                    course=course,
                    professor=professor,
                    topic=topic,
                    week_number=week_number,
                    order_in_week=order_in_week,
                    previous_lecture_content=previous_content,
                    word_count=word_count,
                )

            return lecture

        except Exception as e:
            error_msg = f"Failed to generate lecture content: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e

    async def export_lecture_text(
        self, lecture: Lecture, course: Course, professor: Professor
    ) -> str:
        """
        Export lecture content to a text file and storage.

        Args:
            lecture: Lecture to export
            course: Course the lecture belongs to
            professor: Professor teaching the lecture

        Returns:
            Path to the exported file
        """
        # Generate header and content
        header = self._generate_lecture_file_header(lecture, course, professor)
        full_text = f"{header}\n\n{lecture.content}"

        # Create local file path
        local_file_path = ""
        if self.text_export_path:
            # Ensure export directory exists
            course_dir = os.path.join(self.text_export_path, course.code)
            os.makedirs(course_dir, exist_ok=True)

            # Create local file path
            filename = f"week{lecture.week_number}_lecture{lecture.order_in_week}.md"
            local_file_path = os.path.join(course_dir, filename)

            # Save to local file
            with open(local_file_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            self.logger.info(f"Lecture text exported to {local_file_path}")

        # Upload to storage
        storage_key = self.storage_service.generate_lecture_key(
            course_id=course.code,
            week_number=lecture.week_number,
            lecture_order=lecture.order_in_week,
        )

        # Upload markdown file to storage
        success, storage_url = await self.storage_service.upload_lecture_file(
            file_data=full_text.encode("utf-8"),
            object_name=storage_key,
            content_type="text/markdown",
        )

        if success:
            self.logger.info(f"Lecture text uploaded to storage at {storage_url}")
            return storage_url
        else:
            self.logger.warning("Failed to upload lecture text to storage")
            return local_file_path

    def _generate_lecture_file_header(
        self, lecture: Lecture, course: Course, professor: Professor
    ) -> str:
        """
        Generate the header for the lecture file.

        Args:
            lecture: Lecture object
            course: Course object
            professor: Professor object

        Returns:
            str: Formatted header text
        """
        return f"""# {lecture.title}

## Course: {course.title} ({course.code})
## Professor: {professor.name}
## Week: {lecture.week_number}, Lecture: {lecture.order_in_week}
## Generated with: {self.content_backend}{f" ({self.content_model})" if self.content_model else ""}
## Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""

    def get_lecture_by_course_week_order(
        self, course_id: str, week_number: int, order_in_week: int
    ) -> Lecture:
        """
        Get a lecture by course ID, week number, and order within week.

        Args:
            course_id: Course ID
            week_number: Week number
            order_in_week: Order within week

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository.lecture.get_by_course_week_order(
            course_id=course_id, week_number=week_number, order_in_week=order_in_week
        )
        if not lecture:
            error_msg = f"Lecture for course {course_id}, week {week_number}, number {order_in_week} not found"
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def get_lecture_export_path(self, course_code: str, week: int, number: int) -> str:
        """
        Get the path to the exported lecture file.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week

        Returns:
            Path to the exported file
        """
        if self.text_export_path:
            return os.path.join(
                self.text_export_path, course_code, f"week{week}_lecture{number}.md"
            )
        return ""

    def create_lecture_series(
        self,
        course_code: str,
        topics: List[str],
        starting_week: int = 1,
        word_count: int = DEFAULT_LECTURE_WORD_COUNT,
    ) -> List[Lecture]:
        """
        Generate a series of related lectures for a course using prompt caching.

        This method creates multiple lectures in sequence, maintaining the professor's
        voice and teaching style across all lectures, while building continuity
        between the content. This is more efficient than creating lectures one-by-one
        as it leverages prompt caching for reduced token usage.

        Args:
            course_code: Code for the course to create lectures for
            topics: List of lecture topics in sequence
            starting_week: Week number to start from (default: 1)
            word_count: Target word count for each lecture (default: DEFAULT_LECTURE_WORD_COUNT)

        Returns:
            List of Lecture objects
        """
        # Find the course
        course = self.course_service.get_course_by_code(course_code)
        professor = self.professor_service.get_professor(course.professor_id)

        try:
            # Check if we can use caching
            if self.enable_caching and self.content_backend == "anthropic":
                self.logger.info(
                    f"Generating lecture series for {course.code} with {len(topics)} lectures using caching"
                )

                # Use the lecture series caching method
                lecture_results = (
                    self.content_generator.create_lecture_series_with_caching(
                        course=course,
                        professor=professor,
                        topics=topics,
                        starting_week=starting_week,
                        word_count=word_count,
                    )
                )

                # Store lectures in the database
                lectures = []
                total_tokens_saved = 0

                for lecture_tuple in lecture_results:
                    lecture, metrics = lecture_tuple

                    # Save the lecture to the database
                    lecture = self.repository.lecture.create(lecture)
                    lectures.append(lecture)

                    # Track token savings
                    total_tokens_saved += metrics.get("estimated_tokens_saved", 0)

                # Log total savings
                if total_tokens_saved > 0:
                    self.logger.info(
                        f"Total tokens saved across series: {total_tokens_saved}"
                    )

                return lectures

            else:
                # Use individual lecture creation if caching is not available
                self.logger.info(
                    f"Generating lecture series for {course.code} without caching "
                    f"(not using Anthropic or caching disabled)"
                )

                lectures = []
                previous_lecture = None

                for i, topic in enumerate(topics):
                    week_number = starting_week + (i // course.lectures_per_week)
                    order_in_week = (i % course.lectures_per_week) + 1

                    # Create the lecture
                    lecture = self._create_lecture_content(
                        course=course,
                        professor=professor,
                        topic=topic,
                        week_number=week_number,
                        order_in_week=order_in_week,
                        previous_lecture=previous_lecture,
                        word_count=word_count,
                    )

                    # Save the lecture to the database
                    lecture = self.repository.lecture.create(lecture)
                    lectures.append(lecture)

                    # Update previous lecture for the next iteration
                    previous_lecture = lecture

                return lectures

        except Exception as e:
            error_msg = f"Failed to generate lecture series: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e

    def get_lecture_preview(
        self, course_code: str = None, model_filter: str = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get a preview of lectures with relevant metadata.

        Args:
            course_code: Optional course code to filter lectures
            model_filter: Optional filter to only show lectures from a specific model (e.g., "phi4-mini")
            limit: Maximum number of lectures to return

        Returns:
            List of dictionaries containing lecture info
        """
        self.logger.info(
            f"Getting lecture previews"
            f"{f' for course {course_code}' if course_code else ''}"
            f"{f' with model filter {model_filter}' if model_filter else ''}"
        )

        # Get all lectures
        lectures = []

        try:
            courses = self.repository.course.list()

            for course in courses:
                # Handle either format - dict with "course" key or direct Course object
                if isinstance(course, dict) and "course" in course:
                    course = course["course"]

                # Skip if filtering by course code and this isn't the right course
                if course_code and course.code != course_code:
                    continue

                lectures.extend(self._get_lectures_for_course(course, model_filter))

            # Sort by most recent first
            lectures.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

            # Limit the results
            return lectures[:limit]
        except Exception as e:
            error_msg = f"Failed to get lecture previews: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _get_lectures_for_course(
        self, course: Course, model_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get lecture previews for a specific course.

        Args:
            course: Course object
            model_filter: Optional model filter

        Returns:
            List[Dict[str, Any]]: List of lecture preview dictionaries
        """
        lectures = []

        try:
            professor = self.repository.professor.get(course.professor_id)
            if not professor:
                self.logger.warning(
                    f"Professor not found for course {course.code}, skipping"
                )
                return []

            course_lectures = self.repository.lecture.list_by_course(course.id)

            for lecture in course_lectures:
                # Get model information and skip if it doesn't match the filter
                model_used = self._get_lecture_model_info(course.code, lecture)
                if model_filter and (
                    not model_used or model_filter.lower() not in model_used.lower()
                ):
                    continue

                # Construct lecture preview
                lecture_path = self.get_lecture_export_path(
                    course.code, lecture.week_number, lecture.order_in_week
                )

                lectures.append(
                    {
                        "id": lecture.id,
                        "title": lecture.title,
                        "course_code": course.code,
                        "course_title": course.title,
                        "professor": professor.name,
                        "week": lecture.week_number,
                        "lecture_number": lecture.order_in_week,
                        "content_preview": (
                            lecture.content[:200] + "..." if lecture.content else None
                        ),
                        "generated_at": lecture.generated_at,
                        "model_used": model_used,
                        "text_file": (
                            lecture_path if os.path.exists(lecture_path) else None
                        ),
                        "audio_url": lecture.audio_url,
                    }
                )

            return lectures
        except Exception as e:
            self.logger.warning(
                f"Error getting lectures for course {course.code}: {str(e)}"
            )
            return []

    def _get_lecture_model_info(
        self, course_code: str, lecture: Lecture
    ) -> Optional[str]:
        """
        Extract model information from a lecture file.

        Args:
            course_code: Course code
            lecture: Lecture object

        Returns:
            Optional[str]: Model information if found, None otherwise
        """
        lecture_path = self.get_lecture_export_path(
            course_code, lecture.week_number, lecture.order_in_week
        )

        if not lecture_path or not os.path.exists(lecture_path):
            return None

        try:
            with open(lecture_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Look for the model info in the header
                model_lines = [
                    line for line in content.split("\n") if "Generated with:" in line
                ]
                if model_lines:
                    return model_lines[0].replace("## Generated with:", "").strip()
        except Exception as e:
            self.logger.warning(f"Failed to read lecture file {lecture_path}: {str(e)}")

        return None

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-based)
            size: Number of items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            search_query: Search query for title/description

        Returns:
            List of Lecture objects
        """
        return self.repository.lecture.list(
            page=page,
            size=size,
            course_id=course_id,
            professor_id=professor_id,
            search_query=search_query,
        )

    def count_lectures(
        self,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> int:
        return self.repository.lecture.count(
            course_id=course_id,
            professor_id=professor_id,
            search_query=search_query,
        )
