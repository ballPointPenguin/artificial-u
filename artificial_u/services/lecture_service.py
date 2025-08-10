"""
Lecture management service for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    course_model_to_dict,
    parse_lecture_xml,
    professor_model_to_dict,
    topic_model_to_dict,
    topics_model_to_dict,
)
from artificial_u.models.core import Lecture
from artificial_u.prompts import (
    get_lecture_prompt,
    get_system_prompt,
)
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    LectureNotFoundError,
    detect_truncation,
    ensure_xml_wrapper,
    extract_partial_xml_content,
    extract_xml_between_tags,
)


class LectureService:
    """Service for managing lecture entities."""

    def __init__(
        self,
        content_service,
        course_service,
        professor_service,
        repository_factory,
        logger=None,
        topic_service=None,
    ):
        """
        Initialize the lecture service.

        Args:
            content_service: Content generation service
            course_service: Course management service
            professor_service: Professor management service
            repository_factory: Repository factory instance
            logger: Optional logger instance
            topic_service: Topic management service
        """
        self.content_service = content_service
        self.course_service = course_service
        self.professor_service = professor_service
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)
        self.topic_service = topic_service

    # --- CRUD Methods --- #

    def create_lecture(
        self,
        course_id: int,
        topic_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        audio_url: Optional[str] = None,
        transcript_url: Optional[str] = None,
        revision: Optional[int] = None,
    ) -> Lecture:
        """
        Create a new lecture.

        Args:
            course_id: ID of the course this lecture belongs to
            topic_id: ID of the topic this lecture belongs to
            title: Title of the lecture
            content: Optional lecture content
            summary: Optional lecture summary
            audio_url: Optional URL to audio content
            transcript_url: Optional URL to transcript content
            revision: Optional revision number for the lecture

        Returns:
            Lecture: The created lecture

        Raises:
            DatabaseError: If there's an error saving to the database
        """
        # Create lecture object
        lecture = Lecture(
            course_id=course_id,
            topic_id=topic_id,
            title=title,
            revision=revision,
            content=content,
            summary=summary,
            audio_url=audio_url,
            transcript_url=transcript_url,
        )

        try:
            # Save to database using repository
            created_lecture = self.repository_factory.lecture.create(lecture)
            self.logger.info(f"Created lecture for topic {topic_id}, course {course_id}")
            return created_lecture
        except Exception as e:
            error_msg = f"Failed to create lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_lecture(self, lecture_id: int) -> Lecture:
        """
        Get a lecture by ID.

        Args:
            lecture_id: ID of the lecture

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository_factory.lecture.get(lecture_id)
        if not lecture:
            error_msg = f"Lecture with ID {lecture_id} not found"
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def get_lecture_by_course_week_order(
        self, course_id: int, week_number: int, order_in_week: int
    ) -> Lecture:
        """
        Get a specific lecture by its position in a course.

        Args:
            course_id: ID of the course
            week_number: Week number in the course
            order_in_week: Order of the lecture within the week

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository_factory.lecture.get_by_course_week_order(
            course_id=course_id,
            week_number=week_number,
            order_in_week=order_in_week,
        )
        if not lecture:
            error_msg = (
                f"Lecture not found for course {course_id}, "
                f"week {week_number}, order {order_in_week}"
            )
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Optional filter by course ID
            professor_id: Optional filter by professor ID
            topic_id: Optional filter by topic ID
            search_query: Optional search in title/description

        Returns:
            List[Lecture]: List of lectures

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            lectures = self.repository_factory.lecture.list(
                page=page,
                size=size,
                course_id=course_id,
                professor_id=professor_id,
                topic_id=topic_id,
                search_query=search_query,
            )
            self.logger.debug(f"Found {len(lectures)} lectures")
            return lectures
        except Exception as e:
            error_msg = f"Failed to list lectures: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_lecture(self, lecture_id: int, update_data: Dict[str, Any]) -> Lecture:
        """
        Update a lecture.

        Args:
            lecture_id: ID of the lecture to update
            update_data: Dictionary of fields to update

        Returns:
            Lecture: The updated lecture

        Raises:
            LectureNotFoundError: If lecture not found
            DatabaseError: If there's an error updating the database
        """
        # Get existing lecture
        lecture = self.get_lecture(lecture_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(lecture, key):
                setattr(lecture, key, value)
            else:
                self.logger.warning(f"Ignoring unknown field: {key}")

        try:
            # Save changes
            updated_lecture = self.repository_factory.lecture.update(lecture)
            self.logger.info(f"Updated lecture {lecture_id}")
            return updated_lecture
        except Exception as e:
            error_msg = f"Failed to update lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: ID of the lecture to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            LectureNotFoundError: If lecture not found
            DatabaseError: If there's an error deleting from the database
        """
        # Check if lecture exists
        self.get_lecture(lecture_id)

        try:
            # Delete the lecture
            result = self.repository_factory.lecture.delete(lecture_id)
            if result:
                self.logger.info(f"Lecture {lecture_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    # --- Generation Methods --- #

    def _prepare_prompt_arguments(
        self,
        partial_attributes: Dict[str, Any],
        course_data: Dict[str, Any],
        professor_data: Dict[str, Any],
        topic_data: Dict[str, Any],
        existing_lectures_data: List[Dict[str, Any]],
        all_course_topics_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare arguments for the lecture generation prompt."""
        return {
            "course_data": course_data,
            "professor_data": professor_data,
            "topic_data": topic_data,
            "existing_lectures": existing_lectures_data,
            "topics_data": all_course_topics_data,
            "freeform_prompt": partial_attributes.get("freeform_prompt"),
            "word_count": partial_attributes.get("word_count", 3000),
        }

    async def _generate_and_parse_content(self, prompt_args: Dict[str, Any]) -> str:
        """Generate lecture content and parse the XML response."""
        lecture_prompt = get_lecture_prompt(**prompt_args)
        system_prompt = get_system_prompt("lecture")

        self.logger.info("Calling content service to generate lecture...")
        raw_response = await self.content_service.generate_text(
            model=get_settings().LECTURE_GENERATION_MODEL,
            prompt=lecture_prompt,
            system_prompt=system_prompt,
            max_tokens=16384,  # 2^14
        )
        self.logger.info("Received response from content service.")

        # Check if response appears truncated
        is_truncated = detect_truncation(raw_response)
        if is_truncated:
            self.logger.warning("Response appears to be truncated due to token limits")

        # Simplified XML extraction logic
        generated_xml_output = None

        # First try to extract from <output> tags
        generated_xml_output = extract_xml_between_tags(raw_response, "output")
        if generated_xml_output:
            self.logger.info("Successfully extracted content from <output> tags")
        else:
            self.logger.info("<output> tag not found, trying direct <lecture> extraction...")

            # Check if the response directly contains <lecture>...</lecture>
            if raw_response.strip().startswith("<lecture>") and raw_response.strip().endswith(
                "</lecture>"
            ):
                # Use the raw response directly
                generated_xml_output = raw_response.strip()
                self.logger.info("Using raw response as it contains valid <lecture> structure")
            else:
                # For truncated responses, try to extract partial content
                if is_truncated:
                    # For lectures, we need to handle them differently since they have
                    # a simpler structure with title and content elements
                    generated_xml_output = extract_partial_xml_content(
                        raw_response,
                        root_element="lecture",
                        child_element="content",
                        required_children=None,  # content might be incomplete
                        metadata_tags=["title"],
                    )
                    if not generated_xml_output:
                        # Try a simpler extraction for lecture content
                        import re

                        lecture_match = re.search(
                            r"<lecture>.*?<content>(.*)", raw_response, re.DOTALL
                        )
                        if lecture_match:
                            content = lecture_match.group(1)
                            # Close unclosed tags
                            from artificial_u.utils.xml_utils import close_unclosed_tags

                            content = close_unclosed_tags(content)
                            if not content.endswith("</content>"):
                                content += "</content>"
                            generated_xml_output = f"<lecture>\n<content>{content}</lecture>"
                            self.logger.info(
                                "Recovered partial lecture content from truncated response"
                            )
                    else:
                        self.logger.info("Extracted partial XML from truncated response")
                else:
                    # Try to extract inner content and wrap it
                    inner_content = extract_xml_between_tags(raw_response, "lecture")
                    if inner_content:
                        generated_xml_output = f"<lecture>\n{inner_content}\n</lecture>"
                        self.logger.info("Extracted <lecture> inner content and wrapped it")

        if not generated_xml_output:
            error_msg = (
                f"Could not extract <output> or <lecture> tag from response"
                f"{' (response was truncated)' if is_truncated else ''}:\n"
                f"{raw_response[:500]}..."
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        # Ensure the extracted content has the proper <lecture> wrapper
        generated_xml_output = ensure_xml_wrapper(generated_xml_output, "lecture")

        return generated_xml_output

    def _process_models_for_generation(self, partial_attributes: Dict[str, Any]) -> tuple[
        Dict[str, Any],  # course_dict
        Dict[str, Any],  # professor_dict
        Dict[str, Any],  # topic_dict
        List[Dict[str, Any]],  # existing_lectures_list_of_dicts
        List[Dict[str, Any]],  # all_course_topics_list_of_dicts
    ]:
        """Process course, professor, topic, existing lectures, and all course topics
        for generation."""
        course_id = partial_attributes.get("course_id")
        topic_id = partial_attributes.get("topic_id")

        if not course_id:
            raise ValueError("course_id is required for lecture generation.")
        if not topic_id:
            raise ValueError("topic_id is required for lecture generation.")

        course_dict = self._get_course_data_for_generation(course_id)
        professor_dict = self._get_professor_data_for_generation(course_dict.get("id"))
        current_topic_dict = self._get_current_topic_data_for_generation(topic_id, course_id)
        existing_lectures_list_of_dicts = self._get_existing_lectures_data_for_generation(course_id)
        all_course_topics_list_of_dicts = self._get_all_course_topics_data_for_generation(course_id)

        return (
            course_dict,
            professor_dict,
            current_topic_dict,
            existing_lectures_list_of_dicts,
            all_course_topics_list_of_dicts,
        )

    def _get_course_data_for_generation(self, course_id: int) -> Dict[str, Any]:
        """Fetches and prepares course data for lecture generation."""
        try:
            course = self.course_service.get_course(course_id)
            return course_model_to_dict(course) if course else {}
        except Exception as e:
            self.logger.error(f"Error fetching course {course_id}: {e}")
            raise DatabaseError(f"Error fetching course {course_id}: {e}")

    def _get_professor_data_for_generation(self, course_id: Optional[int]) -> Dict[str, Any]:
        """Fetches and prepares professor data for lecture generation."""
        if not course_id:
            return {}
        try:
            # Need to get the course first to find the professor_id
            course = self.course_service.get_course(course_id)
            if course and course.professor_id:
                professor = self.professor_service.get_professor(course.professor_id)
                return professor_model_to_dict(professor) if professor else {}
            return {}
        except Exception as e:
            self.logger.warning(f"Error fetching professor for course {course_id}: {e}")
            return {}  # Return empty dict on error as per original logic

    def _get_current_topic_data_for_generation(
        self, topic_id: int, course_id: int
    ) -> Dict[str, Any]:
        """Fetches and prepares the current topic data for lecture generation."""
        try:
            current_topic = self.topic_service.get_topic(topic_id)
            if not current_topic or current_topic.course_id != course_id:
                err_msg = f"Topic {topic_id} not found or does not belong to course {course_id}."
                self.logger.error(err_msg)
                raise DatabaseError(err_msg)
            return topic_model_to_dict(current_topic) if current_topic else {}
        except Exception as e:
            self.logger.error(f"Error fetching topic {topic_id}: {e}")
            raise DatabaseError(f"Error fetching topic {topic_id}: {e}")

    def _get_existing_lectures_data_for_generation(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetches and prepares existing lectures data for context."""
        existing_lectures_list_of_dicts = []
        try:
            lectures_core_models = self.repository_factory.lecture.list_by_course(course_id)
            for lec_model in lectures_core_models:
                try:
                    lec_topic = self.topic_service.get_topic(lec_model.topic_id)
                    if lec_topic:
                        existing_lectures_list_of_dicts.append(
                            {
                                "title": lec_topic.title,
                                "week": lec_topic.week,
                                "order": lec_topic.order,
                                "summary": lec_model.summary or "",
                            }
                        )
                    else:
                        self.logger.warning(
                            f"Could not find topic {lec_model.topic_id} for existing lecture "
                            f"{lec_model.id}"
                        )
                except Exception as topic_e:
                    self.logger.error(
                        f"Error fetching topic {lec_model.topic_id} for existing lecture "
                        f"{lec_model.id}: {topic_e}"
                    )
        except Exception as e:
            self.logger.warning(
                f"Error fetching or processing existing lectures for course {course_id}: {e}"
            )
        return existing_lectures_list_of_dicts

    def _get_all_course_topics_data_for_generation(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetches and prepares all course topics data for context."""
        try:
            topics_core_models = self.topic_service.list_topics_by_course(course_id)
            return topics_model_to_dict(topics_core_models)
        except Exception as e:
            self.logger.warning(f"Error fetching all topics for course {course_id}: {e}")
            return []  # Return empty list on error as per original logic

    async def generate_lecture(
        self,
        partial_attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a lecture using AI based on partial attributes.

        Args:
            partial_attributes: Optional dictionary of known attributes to guide generation
                              or fill in the blanks. Expected to contain 'course_id' and 'topic_id'.

        Returns:
            Dict[str, Any]: The generated lecture attributes.

        Raises:
            ContentGenerationError: If content generation or parsing fails.
            DatabaseError: If there's an error fetching prerequisite data.
            ValueError: If required partial_attributes are missing.
        """
        partial_attributes = partial_attributes or {}
        self.logger.info(
            "Generating lecture content with partial attributes: "
            f"{list(partial_attributes.keys())}"
        )

        try:
            # Process models and prepare data for generation
            (
                course_dict,
                professor_dict,
                current_topic_dict,
                existing_lectures_data,
                all_course_topics_data,
            ) = self._process_models_for_generation(partial_attributes)

            # Prepare prompt arguments
            prompt_args = self._prepare_prompt_arguments(
                partial_attributes,
                course_dict,
                professor_dict,
                current_topic_dict,
                existing_lectures_data,
                all_course_topics_data,
            )

            # Generate and parse content
            generated_xml_output = await self._generate_and_parse_content(prompt_args)
            self.logger.debug(f"Generated XML for lecture: {generated_xml_output[:500]}...")

            # Parse XML and combine with partial attributes
            # parse_lecture_xml is expected to return {'content': '...'}
            parsed_lecture_data = parse_lecture_xml(generated_xml_output)

            if parsed_lecture_data.get("content") is None:
                error_msg = (
                    "Failed to extract valid <content> from generated XML. "
                    f"Input XML: {generated_xml_output[:500]}..."
                )
                self.logger.error(error_msg)
                raise ContentGenerationError(error_msg)

            # final_lecture_data should be built based on Lecture model fields
            final_lecture_data = {
                "course_id": partial_attributes.get("course_id"),
                "topic_id": partial_attributes.get("topic_id"),
                "revision": partial_attributes.get("revision"),
                "summary": partial_attributes.get("summary"),
                "title": parsed_lecture_data.get("title"),
                "content": parsed_lecture_data.get("content"),
            }

            # Add other relevant fields from partial_attributes if they are valid for Lecture model
            for key in ["audio_url", "transcript_url"]:
                if key in partial_attributes:
                    final_lecture_data[key] = partial_attributes[key]

            # Filter final_lecture_data to include only valid LectureModel fields
            from artificial_u.models.database import LectureModel  # Keep import local for clarity

            valid_lecture_keys = {c.name for c in LectureModel.__table__.columns}
            final_lecture_data = {
                k: v for k, v in final_lecture_data.items() if k in valid_lecture_keys
            }

            self.logger.info(
                "Successfully generated lecture content for topic "
                f"{final_lecture_data.get('topic_id')}"
            )
            return final_lecture_data

        except ContentGenerationError:
            # Let content generation errors propagate up
            raise
        except ValueError as e:
            raise ContentGenerationError(f"Error generating/parsing lecture: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during lecture generation: {e}", exc_info=True)
            raise ContentGenerationError(f"An unexpected error occurred: {e}")

    # ===== Audio Generation (helpers) ===== #

    def _fetch_entities_for_audio(self, lecture_id: int):
        """Fetch lecture, course, topic, professor for audio generation."""
        lecture = self.get_lecture(lecture_id)
        if not lecture or not lecture.content:
            raise ContentGenerationError("Lecture content is missing; cannot generate audio")

        course = self.course_service.get_course(lecture.course_id)
        if not course:
            raise DatabaseError(f"Course {lecture.course_id} not found for lecture {lecture_id}")

        topic = self.topic_service.get_topic(lecture.topic_id)
        if not topic:
            raise DatabaseError(f"Topic {lecture.topic_id} not found for lecture {lecture_id}")

        if not course.professor_id:
            raise DatabaseError("Course has no professor assigned; cannot select a voice")
        professor = self.professor_service.get_professor(course.professor_id)
        if not professor:
            raise DatabaseError(f"Professor {course.professor_id} not found for course {course.id}")

        return lecture, course, topic, professor

    def _ensure_professor_el_voice_id(self, professor) -> str:
        """Resolve or auto-assign an ElevenLabs voice id for the professor."""
        el_voice_id: Optional[str] = None
        if professor.voice_id:
            voice_repo = self.repository_factory.voice
            voice = voice_repo.get(professor.voice_id)
            el_voice_id = voice.el_voice_id if voice else None

        if not el_voice_id:
            from artificial_u.services.voice_service import VoiceService

            voice_service = VoiceService(
                repository_factory=self.repository_factory,
                logger=self.logger,
            )
            selected = voice_service.select_voice_for_professor(professor)
            el_voice_id = selected.get("el_voice_id")
            if not el_voice_id:
                raise DatabaseError("Failed to select or resolve an ElevenLabs voice ID")

        return el_voice_id

    def _generate_audio_bytes(self, lecture, professor, el_voice_id: str) -> bytes:
        """Use TTSService to generate audio bytes for a lecture."""
        from artificial_u.config import get_settings
        from artificial_u.services.tts_service import TTSService

        settings = get_settings()

        tts_service = TTSService(
            api_key=settings.ELEVENLABS_API_KEY,
            audio_path=None,
            repository_factory=self.repository_factory,
            logger=self.logger,
        )
        try:
            _file_path, audio_bytes = tts_service.generate_lecture_audio(
                lecture=lecture,
                professor=professor,
                el_voice_id=el_voice_id,
                save_to_file=False,
            )
            return audio_bytes
        except Exception as e:
            raise ContentGenerationError(f"TTS generation failed: {e}")

    async def _upload_audio_and_get_url(self, course, topic, audio_bytes: bytes) -> str:
        """Upload audio to storage and return the public URL."""
        from artificial_u.services.storage_service import StorageService

        storage_service = StorageService(logger=self.logger)
        course_code = getattr(course, "code", str(course.id))
        week = getattr(topic, "week", 1)
        number = getattr(topic, "order", 1)
        object_key = storage_service.generate_audio_key(
            course_code=str(course_code),
            week_number=int(week),
            lecture_order=int(number),
        )
        success, audio_url = await storage_service.upload_audio_file(
            file_data=audio_bytes,
            object_name=object_key,
            content_type="audio/mpeg",
        )
        if not success or not audio_url:
            raise DatabaseError("Failed to upload generated audio to storage")
        return audio_url

    async def generate_lecture_audio(self, lecture_id: int) -> Dict[str, Any]:
        """Generate and store audio for the given lecture, updating audio_url."""
        # 1. Fetch required entities
        lecture, course, topic, professor = self._fetch_entities_for_audio(lecture_id)

        # 2. Ensure we have an ElevenLabs voice id
        el_voice_id = self._ensure_professor_el_voice_id(professor)

        # 3. Generate audio bytes
        audio_bytes = self._generate_audio_bytes(lecture, professor, el_voice_id)

        # 4. Upload to storage and get public URL
        audio_url = await self._upload_audio_and_get_url(course, topic, audio_bytes)

        # 5. Update lecture with audio URL (force update if one existed)
        lecture.audio_url = audio_url
        updated = self.repository_factory.lecture.update(lecture)
        self.logger.info(
            "Generated audio for lecture %s and uploaded to storage: %s",
            lecture_id,
            audio_url,
        )

        return {"lecture_id": updated.id, "audio_url": updated.audio_url}
