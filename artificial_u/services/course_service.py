"""
Course management service for ArtificialU.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.config.defaults import DEFAULT_COURSE_WEEKS, DEFAULT_LECTURES_PER_WEEK
from artificial_u.models.core import Course, Professor
from artificial_u.prompts.base import extract_xml_content
from artificial_u.prompts.courses import get_course_topics_prompt
from artificial_u.utils.exceptions import (
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
)


class CourseService:
    """Service for managing course entities."""

    def __init__(self, repository, content_service, professor_service, logger=None):
        """
        Initialize the course service.

        Args:
            repository: Data repository
            content_service: Content generation service
            professor_service: Professor management service
            logger: Optional logger instance
        """
        self.repository = repository
        self.content_service = content_service
        self.professor_service = professor_service
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    def create_course(
        self,
        title: str,
        code: str,
        department_id: str,
        level: str,
        professor_id: Optional[str] = None,
        description: Optional[str] = None,
        credits: Optional[int] = 3,
        weeks: int = DEFAULT_COURSE_WEEKS,
        lectures_per_week: int = DEFAULT_LECTURES_PER_WEEK,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Course, Professor]:
        """
        Create a new course without generating content.

        Args:
            title: Course title
            code: Course code (e.g., "CS101")
            department_id: ID of existing department
            level: Course level (Undergraduate, Graduate, etc.)
            professor_id: ID of existing professor
            description: Course description
            credits: Number of credits for the course (default: 3)
            weeks: Number of weeks in the course
            lectures_per_week: Number of lectures per week
            topics: Optional pre-defined topics structure

        Returns:
            Tuple: (Course, Professor) - The created course and its professor
        """
        self.logger.info(f"Creating new course: {code} - {title}")

        # Get or create professor
        professor = self.professor_service.get_or_create_professor(professor_id)

        # Create basic course
        course = Course(
            code=code,
            title=title,
            department_id=department_id,
            level=level,
            professor_id=professor.id,
            description=description,
            credits=credits,
            total_weeks=weeks,
            lectures_per_week=lectures_per_week,
            topics=topics,
        )

        # Save to database
        try:
            course = self.repository.course.create(course)
            self.logger.info(f"Course created with ID: {course.id}")
            return course, professor
        except Exception as e:
            error_msg = f"Failed to save course: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_course(self, course_id: str) -> Course:
        """
        Get a course by ID.

        Args:
            course_id: ID of the course

        Returns:
            Course: The course object

        Raises:
            CourseNotFoundError: If course not found
        """
        course = self.repository.course.get(course_id)
        if not course:
            error_msg = f"Course with ID {course_id} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)
        return course

    def get_course_by_code(self, course_code: str) -> Course:
        """
        Get a course by its code.

        Args:
            course_code: Course code to look up

        Returns:
            Course: The course object

        Raises:
            CourseNotFoundError: If course not found
        """
        course = self.repository.course.get_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)
        return course

    def list_courses(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all courses with professor information.

        Args:
            department: Optional department to filter by

        Returns:
            List[Dict]: List of courses with professor information
        """
        self.logger.info(
            f"Listing courses{f' for department {department}' if department else ''}"
        )

        try:
            courses = self.repository.course.list(department)
            result = []

            for course in courses:
                professor = self.repository.professor.get(course.professor_id)
                result.append({"course": course, "professor": professor})

            self.logger.debug(f"Found {len(result)} courses")
            return result
        except Exception as e:
            error_msg = f"Failed to list courses: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_course(self, course_id: str, update_data: Dict[str, Any]) -> Course:
        """
        Update a course.

        Args:
            course_id: ID of the course to update
            update_data: Dictionary of fields to update

        Returns:
            Course: The updated course

        Raises:
            CourseNotFoundError: If course not found
            DatabaseError: If there's an error updating the database
        """
        # Get existing course
        course = self.get_course(course_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(course, key):
                setattr(course, key, value)
            else:
                self.logger.warning(f"Ignoring unknown field: {key}")

        # Save changes
        try:
            updated_course = self.repository.course.update(course)
            return updated_course
        except Exception as e:
            error_msg = f"Failed to update course: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_course(self, course_id: str) -> bool:
        """
        Delete a course.

        Args:
            course_id: ID of the course to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            CourseNotFoundError: If course not found
            DatabaseError: If there's an error deleting from the database
        """
        # Check if course exists
        self.get_course(course_id)

        # Delete the course
        try:
            result = self.repository.course.delete(course_id)
            if result:
                self.logger.info(f"Course {course_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete course: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    # --- Generation Methods --- #

    async def generate_course_topics(self, course_id: str) -> Course:
        """
        Generate topics for an existing course and update the course.

        Args:
            course_id: ID of the course to generate topics for

        Returns:
            Course: The updated course with generated topics

        Raises:
            CourseNotFoundError: If course not found
            ContentGenerationError: If topics generation fails
            DatabaseError: If there's an error updating the database
        """
        # Get the course
        course = self.get_course(course_id)

        # Get professor if one is assigned, but don't require it
        professor = None
        if course.professor_id:
            professor = self.repository.professor.get(course.professor_id)
            self.logger.debug(
                f"Found professor {professor.name} for course {course_id}"
            )
        else:
            self.logger.debug(f"No professor assigned to course {course_id}")

        try:
            # Generate topics content
            topics_content = await self._generate_course_topics_content(
                course, professor
            )

            # Parse the topics XML into a structured format
            parsed_topics = self._parse_topics_xml(
                topics_content, course.total_weeks, course.lectures_per_week
            )

            # Update the course with the generated topics
            updated_course = self.update_course(
                course_id=course_id, update_data={"topics": parsed_topics}
            )

            self.logger.info(f"Topics generated and updated for course {course_id}")
            return updated_course
        except ContentGenerationError:
            # Re-raise content generation errors
            raise
        except Exception as e:
            error_msg = f"Failed to generate and update course topics: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e

    async def generate_course_content(self, course_id: str) -> Course:
        """
        Generate both topics for an existing course.

        Args:
            course_id: ID of the course to generate content for

        Returns:
            Course: The updated course with generated content

        Raises:
            CourseNotFoundError: If course not found
            ContentGenerationError: If content generation fails
            DatabaseError: If there's an error updating the database
        """
        # Generate topics
        await self.generate_course_topics(course_id)

    async def _generate_course_topics_content(
        self, course: Course, professor: Optional[Professor] = None
    ) -> str:
        """
        Generate structured topics XML for a course.

        Args:
            course: Course object
            professor: Optional professor object

        Returns:
            str: The generated topics XML

        Raises:
            ContentGenerationError: If generation fails
        """
        self.logger.debug(f"Generating topics for course {course.code}")

        try:
            # Prepare the prompt with professor info if available
            topics_prompt = get_course_topics_prompt(
                course_title=course.title,
                course_code=course.code,
                department=course.department_id,
                professor_name=professor.name if professor else None,
                teaching_style=professor.teaching_style if professor else None,
                course_description=course.description,
                num_weeks=course.total_weeks,
                topics_per_week=course.lectures_per_week,
            )

            # Generate topics XML
            xml_response = await self.content_service.generate_text(
                prompt=topics_prompt,
                system_prompt="You are an expert curriculum designer for higher education.",
            )

            # Extract topics from XML
            topics_xml = extract_xml_content(xml_response, "course_topics")
            if not topics_xml:
                raise ValueError("Failed to extract course_topics from response")

            return topics_xml

        except Exception as e:
            self.logger.error(
                f"Failed to generate course topics: {str(e)}", exc_info=True
            )
            raise ContentGenerationError(f"Topics generation failed: {str(e)}") from e

    def _parse_topics_xml(
        self, topics_xml: str, total_weeks: int, lectures_per_week: int
    ) -> List[Dict[str, Any]]:
        """
        Parse the topics XML into a JSON structure for storage.

        Args:
            topics_xml: XML string containing topic structure
            total_weeks: Expected number of weeks
            lectures_per_week: Expected lectures per week

        Returns:
            List of week dictionaries with lecture topics
        """
        try:
            # Parse XML
            root = ET.fromstring(f"<root>{topics_xml}</root>")

            # Extract weeks and topics
            weeks_elements = root.findall(".//week")

            result = []
            for week_elem in weeks_elements:
                week_num = int(week_elem.get("number", 0))
                if 1 <= week_num <= total_weeks:
                    week_data = {"week": week_num, "lectures": []}

                    # Find topic elements directly under this week
                    topic_elements = week_elem.findall("./topic")

                    # For backwards compatibility with multiple formats
                    if not topic_elements:
                        # Try to find lecture elements
                        lecture_elements = week_elem.findall("./lecture")
                        for idx, lecture_elem in enumerate(lecture_elements, 1):
                            title = (
                                lecture_elem.text.strip()
                                if lecture_elem.text
                                else f"Week {week_num}, Lecture {idx}"
                            )
                            week_data["lectures"].append(
                                {"number": idx, "title": title}
                            )
                    else:
                        # Process topic elements directly
                        for idx, topic_elem in enumerate(topic_elements, 1):
                            if idx <= lectures_per_week:
                                title = (
                                    topic_elem.text.strip()
                                    if topic_elem.text
                                    else f"Week {week_num}, Lecture {idx}"
                                )
                                week_data["lectures"].append(
                                    {"number": idx, "title": title}
                                )

                    # Ensure we have the right number of lectures per week
                    while len(week_data["lectures"]) < lectures_per_week:
                        idx = len(week_data["lectures"]) + 1
                        week_data["lectures"].append(
                            {"number": idx, "title": f"Week {week_num}, Lecture {idx}"}
                        )

                    # Only keep the expected number of lectures per week
                    week_data["lectures"] = week_data["lectures"][:lectures_per_week]

                    result.append(week_data)

            # Ensure we have entries for all weeks
            existing_weeks = {w["week"] for w in result}
            for week_num in range(1, total_weeks + 1):
                if week_num not in existing_weeks:
                    week_data = {"week": week_num, "lectures": []}
                    for idx in range(1, lectures_per_week + 1):
                        week_data["lectures"].append(
                            {"number": idx, "title": f"Week {week_num}, Lecture {idx}"}
                        )
                    result.append(week_data)

            # Sort by week number
            result.sort(key=lambda w: w["week"])

            return result

        except Exception as e:
            self.logger.error(f"Failed to parse topics XML: {str(e)}", exc_info=True)
            # Return default structure if parsing fails
            return self._generate_default_topics(total_weeks, lectures_per_week)

    def _generate_default_topics(
        self, total_weeks: int, lectures_per_week: int
    ) -> List[Dict[str, Any]]:
        """
        Generate a default topic structure if parsing fails.

        Args:
            total_weeks: Number of weeks in the course
            lectures_per_week: Number of lectures per week

        Returns:
            Default topic structure
        """
        result = []
        for week in range(1, total_weeks + 1):
            week_data = {"week": week, "lectures": []}
            for lecture in range(1, lectures_per_week + 1):
                week_data["lectures"].append(
                    {"number": lecture, "title": f"Week {week}, Lecture {lecture}"}
                )
            result.append(week_data)
        return result
