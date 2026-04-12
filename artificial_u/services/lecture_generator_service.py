"""
Lecture generation service for ArtificialU.

This service handles AI-powered lecture generation, including content generation,
audio generation, summary generation, and associated workflows like file uploads
and background job enqueueing.
"""

import asyncio
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
from artificial_u.prompts.summary import get_summary_prompt
from artificial_u.prompts.system import SUMMARY_SYSTEM_PROMPT
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    LectureNotFoundError,
    detect_truncation,
    ensure_xml_wrapper,
    extract_partial_xml_content,
    extract_xml_between_tags,
)


class LectureGeneratorService:
    """Service for AI-powered lecture generation and processing."""

    def __init__(
        self,
        lecture_service,
        content_service,
        course_service,
        professor_service,
        repository_factory,
        topic_service,
        job_enqueue_service,
        preference_service=None,
        storage_service=None,
        logger=None,
    ):
        """
        Initialize the lecture generator service.

        Args:
            lecture_service: Core lecture service for CRUD operations
            content_service: Content generation service
            course_service: Course management service
            professor_service: Professor management service
            repository_factory: Repository factory instance
            topic_service: Topic management service
            job_enqueue_service: Job enqueueing service for background tasks
            preference_service: Preference service for retrieving model preferences (optional)
            storage_service: Storage service for file operations (optional)
            logger: Optional logger instance
        """
        self.lecture_service = lecture_service
        self.content_service = content_service
        self.course_service = course_service
        self.professor_service = professor_service
        self.repository_factory = repository_factory
        self.topic_service = topic_service
        self.job_enqueue_service = job_enqueue_service
        self.storage_service = storage_service
        self.logger = logger or logging.getLogger(__name__)

        # Initialize preference service or create one
        if preference_service is None:
            from artificial_u.services.preference_service import PreferenceService

            self.preference_service = PreferenceService(repository_factory, logger=self.logger)
        else:
            self.preference_service = preference_service

    # --- Core Generation Methods --- #

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

        # Get the lecture generation model from preferences or settings
        student_id = partial_attributes.get("created_by")
        model = self.preference_service.get_lecture_generation_model(student_id=student_id)

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

            # Generate and parse content with the selected model
            generated_xml_output = await self._generate_and_parse_content(prompt_args, model)
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
                "created_with": model,  # Record the model used for generation
            }

            # Add other relevant fields from partial_attributes if they are valid for Lecture model
            for key in ["audio_url", "transcript_url", "created_by"]:
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

    async def generate_and_save_lecture(
        self,
        partial_attributes: Optional[Dict[str, Any]] = None,
    ) -> Lecture:
        """
        Generate lecture content using AI and save it as a complete lecture record.

        This method orchestrates the complete workflow by delegating to helper methods.

        Args:
            partial_attributes: Optional dictionary of known attributes to guide generation

        Returns:
            Lecture: The complete saved lecture object

        Raises:
            ContentGenerationError: If content generation or parsing fails
            DatabaseError: If there's an error saving to database
            ValueError: If required partial_attributes are missing
        """
        # Generate the content using AI
        generated_dict = await self.generate_lecture(partial_attributes)

        # Calculate revision number and create lecture
        revision = self._calculate_revision_number(generated_dict)
        saved_lecture = self._create_lecture_from_generated_data(generated_dict, revision)

        # Upload transcript and update lecture with URL
        saved_lecture = await self._upload_and_update_transcript(saved_lecture, generated_dict)

        # Enqueue background processing jobs
        self._enqueue_background_jobs_for_lecture(saved_lecture)

        self.logger.info(
            f"Successfully generated and saved lecture {saved_lecture.id} "
            f"for topic {saved_lecture.topic_id}"
        )
        return saved_lecture

    async def generate_and_save_lecture_text_only(
        self,
        partial_attributes: Optional[Dict[str, Any]] = None,
    ) -> Lecture:
        """
        Generate lecture content using AI and save it as a complete lecture record,
        without enqueueing background jobs (audio/summary generation).

        This method is useful when you only want to generate the lecture text content
        without automatically triggering audio and summary generation.

        Args:
            partial_attributes: Optional dictionary of known attributes to guide generation

        Returns:
            Lecture: The complete saved lecture object

        Raises:
            ContentGenerationError: If content generation or parsing fails
            DatabaseError: If there's an error saving to database
            ValueError: If required partial_attributes are missing
        """
        # Generate the content using AI
        generated_dict = await self.generate_lecture(partial_attributes)

        # Calculate revision number and create lecture
        revision = self._calculate_revision_number(generated_dict)
        saved_lecture = self._create_lecture_from_generated_data(generated_dict, revision)

        # Upload transcript and update lecture with URL
        saved_lecture = await self._upload_and_update_transcript(saved_lecture, generated_dict)

        # NOTE: Do NOT enqueue background processing jobs (audio/summary)

        self.logger.info(
            f"Successfully generated and saved lecture text only {saved_lecture.id} "
            f"for topic {saved_lecture.topic_id}"
        )
        return saved_lecture

    # --- Helper Methods for generate_and_save_lecture --- #

    def _calculate_revision_number(self, generated_dict: Dict[str, Any]) -> int:
        """Calculate the revision number for a new lecture."""
        revision = generated_dict.get("revision")
        if revision is not None:
            return revision

        try:
            # Get the maximum revision for this specific topic
            topic_lectures = self.repository_factory.lecture.list_by_topic(
                generated_dict.get("topic_id")
            )
            max_revision = (
                max([lecture.revision for lecture in topic_lectures]) if topic_lectures else 0
            )
            return max_revision + 1
        except Exception:
            # Fallback to 1 if we can't calculate
            return 1

    def _create_lecture_from_generated_data(
        self, generated_dict: Dict[str, Any], revision: int
    ) -> Lecture:
        """Create and save a lecture from generated data."""
        return self.lecture_service.create_lecture(
            course_id=generated_dict.get("course_id"),
            topic_id=generated_dict.get("topic_id"),
            title=generated_dict.get("title"),
            content=generated_dict.get("content"),
            summary=generated_dict.get("summary"),
            audio_url=generated_dict.get("audio_url"),
            transcript_url=generated_dict.get("transcript_url"),
            revision=revision,
            created_by=generated_dict.get("created_by"),
            created_with=generated_dict.get("created_with"),  # Use the model from generated_dict
        )

    async def _upload_and_update_transcript(
        self, saved_lecture: Lecture, generated_dict: Dict[str, Any]
    ) -> Lecture:
        """Upload transcript to storage and update lecture with URL."""
        if not self.storage_service:
            return saved_lecture

        content_text = generated_dict.get("content")
        if not content_text:
            return saved_lecture

        upload_url = await self._upload_transcript_and_get_url(
            course_id=generated_dict.get("course_id"),
            topic_id=generated_dict.get("topic_id"),
            content_text=content_text,
        )

        if upload_url:
            return self.lecture_service.update_lecture(
                lecture_id=saved_lecture.id,
                update_data={"transcript_url": upload_url},
            )
        return saved_lecture

    def _enqueue_background_jobs_for_lecture(self, saved_lecture: Lecture) -> None:
        """Enqueue background processing jobs for a lecture."""
        if get_settings().testing:
            return

        if not saved_lecture.content or not str(saved_lecture.content).strip():
            self.logger.debug(
                "Skipping background job generation: empty content for lecture %s",
                saved_lecture.id,
            )
            return

        # Enqueue summary generation job
        try:
            self.job_enqueue_service.enqueue_lecture_summary_generation(
                saved_lecture.id, topic_id=saved_lecture.topic_id
            )
        except Exception as e:
            self.logger.error(
                "Failed to enqueue summary generation for generated lecture %s: %s",
                saved_lecture.id,
                e,
            )

        # Enqueue audio generation job (can run in parallel to summary)
        try:
            self.job_enqueue_service.enqueue_lecture_audio_generation(
                saved_lecture.id, topic_id=saved_lecture.topic_id
            )
        except Exception as e:
            self.logger.error(
                "Failed to enqueue audio generation for generated lecture %s: %s",
                saved_lecture.id,
                e,
            )

    async def generate_lecture_summary(self, lecture_id: int) -> Dict[str, Any]:
        """Generate and store a concise summary for a lecture.

        Args:
            lecture_id: The ID of the lecture to summarize

        Returns:
            Dict[str, Any]: A dictionary containing the lecture ID and generated summary

        Raises:
            ContentGenerationError: If summary generation fails or content is missing
            LectureNotFoundError: If the lecture cannot be found
        """
        # Fetch lecture and validate content exists
        lecture = self.lecture_service.get_lecture(lecture_id)
        if not lecture:
            raise LectureNotFoundError(f"Lecture with ID {lecture_id} not found")
        if not lecture.content or not str(lecture.content).strip():
            self.logger.warning(
                "Skipping summary generation: lecture %s has no content",
                lecture_id,
            )
            return {"lecture_id": lecture_id, "summary": None}

        # Build prompt and system instruction
        prompt = get_summary_prompt(lecture_content=lecture.content)
        system_prompt = SUMMARY_SYSTEM_PROMPT

        # Generate summary via content service
        self.logger.info("Calling content service to generate lecture summary...")
        raw_response = await self.content_service.generate_text(
            model=get_settings().LECTURE_SUMMARY_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
        )
        self.logger.info("Received summary response from content service.")

        # Extract the inner content from <summary> tag
        summary_text = extract_xml_between_tags(raw_response, "summary")
        if not summary_text:
            error_msg = (
                "Could not extract <summary> tag from response:\n" f"{raw_response[:300]}..."
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        # Partial update to avoid clobbering concurrent changes
        updated = self.repository_factory.lecture.update_fields(
            lecture_id=lecture_id,
            update_data={"summary": summary_text},
        )
        self.logger.info("Generated summary for lecture %s", lecture_id)

        return {"lecture_id": updated.id, "topic_id": updated.topic_id, "summary": updated.summary}

    async def generate_lecture_audio(self, lecture_id: int) -> Dict[str, Any]:
        """Generate and store audio for the given lecture, updating audio_url and voice_id."""
        # 1. Fetch required entities
        lecture, course, topic, professor = self._fetch_entities_for_audio(lecture_id)

        # 2. Resolve the professor's voice and TTS backend
        voice_identifier, voice_id, backend_name = self._ensure_professor_voice(professor)

        # 3. Generate audio bytes (blocking TTS executed in a thread)
        audio_bytes = await asyncio.to_thread(
            self._generate_audio_bytes, lecture, professor, voice_identifier, backend_name
        )

        # 4. Add ID3 metadata tags to audio
        audio_bytes = self._add_id3_tags_to_audio(
            lecture, course, topic, audio_bytes, tts_backend=backend_name
        )

        # 4b. Extract audio duration
        from artificial_u.audio import ID3Tagger

        tagger = ID3Tagger(logger=self.logger)
        duration_seconds = tagger.get_duration_seconds(audio_bytes)

        # 5. Upload to storage and get public URL
        audio_url = await self._upload_audio_and_get_url(course, topic, audio_bytes)

        # 6. Partial update lecture with audio URL, voice_id, and duration (avoid clobbering summary)
        update_data = {"audio_url": audio_url}
        if voice_id:
            update_data["voice_id"] = voice_id
        if duration_seconds is not None:
            update_data["duration"] = duration_seconds

        updated = self.repository_factory.lecture.update_fields(
            lecture_id=lecture_id,
            update_data=update_data,
        )
        self.logger.info(
            "Generated audio for lecture %s using voice %s and uploaded to storage: %s",
            lecture_id,
            voice_id,
            audio_url,
        )

        return {
            "lecture_id": updated.id,
            "topic_id": updated.topic_id,
            "audio_url": updated.audio_url,
            "voice_id": updated.voice_id,
            "duration": updated.duration,
        }

    # --- Helper Methods for Generation --- #

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

    async def _generate_and_parse_content(self, prompt_args: Dict[str, Any], model: str) -> str:
        """Generate lecture content and parse the XML response."""
        lecture_prompt = get_lecture_prompt(**prompt_args)
        system_prompt = get_system_prompt("lecture")

        self.logger.info(f"Calling content service to generate lecture with model: {model}...")
        raw_response = await self.content_service.generate_text(
            model=model,
            prompt=lecture_prompt,
            system_prompt=system_prompt,
            max_tokens=16384,  # 2^14
            prefill="<lecture_outline>",  # No trailing whitespace
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
        # Exclude current and future topics from existing lectures context if we know week/order
        current_week = current_topic_dict.get("week")
        current_order = current_topic_dict.get("order")
        existing_lectures_list_of_dicts = self._get_existing_lectures_data_for_generation(
            course_id=course_id,
            current_week=current_week,
            current_order=current_order,
        )
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

    def _get_existing_lectures_data_for_generation(
        self,
        course_id: int,
        current_week: Optional[int] = None,
        current_order: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetches and prepares existing lectures data for context.

        If current_week and current_order are provided, filter OUT:
          - any lecture with week > current_week
          - any lecture with week == current_week and order >= current_order
        This removes the current and any future topics from the context list.
        """
        existing_lectures_list_of_dicts = []
        try:
            lectures_core_models = self.repository_factory.lecture.list_by_course(course_id)
            for lec_model in lectures_core_models:
                try:
                    lec_topic = self.topic_service.get_topic(lec_model.topic_id)
                    if lec_topic:
                        # Apply filtering if we know the current position
                        if current_week is not None and current_order is not None:
                            try:
                                topic_week = int(getattr(lec_topic, "week", 0) or 0)
                                topic_order = int(getattr(lec_topic, "order", 0) or 0)
                                if (topic_week > int(current_week)) or (
                                    topic_week == int(current_week)
                                    and topic_order >= int(current_order)
                                ):
                                    # Skip current and future topics
                                    continue
                            except Exception:
                                # If parsing fails, do not filter this item
                                pass
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

    async def _upload_transcript_and_get_url(
        self,
        course_id: int,
        topic_id: int,
        content_text: str,
    ) -> Optional[str]:
        """Upload generated lecture text to storage and return its URL.

        The text is normalized for TTS compatibility before being uploaded as a transcript.
        This ensures that users can submit the transcript to external TTS services
        and get good results.
        """
        if not self.storage_service or not content_text:
            return None

        try:
            # Normalize text for TTS compatibility before uploading as transcript
            from artificial_u.audio.speech_processor import SpeechProcessor

            speech_processor = SpeechProcessor(logger=self.logger)
            normalized_text = speech_processor.normalize_text(content_text)
            course = self.course_service.get_course(course_id)
            topic = self.topic_service.get_topic(topic_id)

            course_code = str(getattr(course, "code", None) or getattr(course, "id"))
            week_number = int(getattr(topic, "week", 1))
            lecture_order = int(getattr(topic, "order", 1))

            object_key = self.storage_service.generate_lecture_key(
                course_code=course_code,
                week_number=week_number,
                lecture_order=lecture_order,
                extension="txt",
            )

            success, url = await self.storage_service.upload_lecture_file(
                file_data=normalized_text.encode("utf-8"),
                object_name=object_key,
                content_type="text/plain",
            )
            return url if success else None
        except Exception as e:
            self.logger.error("Transcript upload failed: %s", e, exc_info=True)
            return None

    # --- Audio Generation Helper Methods --- #

    def _fetch_entities_for_audio(self, lecture_id: int):
        """Fetch lecture, course, topic, professor for audio generation."""
        lecture = self.lecture_service.get_lecture(lecture_id)
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

    def _ensure_professor_voice(self, professor) -> tuple[str, Optional[int], str]:
        """Resolve or auto-assign a voice for the professor.

        Returns:
            A tuple of (voice_identifier, voice_id, backend_name) where:
            - voice_identifier is the provider-specific voice ID
            - voice_id is the database ID
            - backend_name is the TTS backend (e.g., 'elevenlabs', 'mistral')
        """
        voice_identifier: Optional[str] = None
        voice_id: Optional[int] = None
        # Professor-level override takes priority, then voice record, then system default
        backend_name = getattr(professor, "tts_backend", None) or "elevenlabs"

        if professor.voice_id:
            voice_repo = self.repository_factory.voice
            voice = voice_repo.get(professor.voice_id)
            if voice:
                # Only use voice record's backend if professor doesn't override
                if not getattr(professor, "tts_backend", None):
                    backend_name = voice.tts_backend or "elevenlabs"
                voice_id = voice.id
                # Use the appropriate identifier for the backend
                if backend_name == "elevenlabs":
                    voice_identifier = voice.el_voice_id or voice.external_id
                else:
                    voice_identifier = voice.external_id or voice.el_voice_id

        if not voice_identifier:
            # Auto-assign via VoiceService (currently only supports ElevenLabs)
            from artificial_u.integrations import elevenlabs
            from artificial_u.services.voice_service import VoiceService

            settings = get_settings()
            elevenlabs_client = None
            if settings.ELEVENLABS_API_KEY:
                try:
                    elevenlabs_client = elevenlabs.ElevenLabsClient(
                        api_key=settings.ELEVENLABS_API_KEY
                    )
                except Exception as e:
                    self.logger.error(f"Failed to create ElevenLabs client: {e}")

            voice_service = VoiceService(
                repository_factory=self.repository_factory,
                client=elevenlabs_client,
                logger=self.logger,
            )
            selected = voice_service.select_voice_for_professor(professor)
            voice_identifier = selected.get("el_voice_id")
            voice_id = selected.get("db_voice_id")
            backend_name = "elevenlabs"
            if not voice_identifier:
                raise DatabaseError("Failed to select or resolve a voice ID")

        return voice_identifier, voice_id, backend_name

    # Backward-compatible alias
    def _ensure_professor_el_voice_id(self, professor) -> tuple[str, Optional[int]]:
        """Legacy wrapper - returns (el_voice_id, voice_id)."""
        voice_id_str, db_voice_id, _ = self._ensure_professor_voice(professor)
        return voice_id_str, db_voice_id

    def _generate_audio_bytes(
        self, lecture, professor, el_voice_id: str, backend_name: str = "elevenlabs"
    ) -> bytes:
        """Use TTSService to generate audio bytes for a lecture."""
        from artificial_u.integrations.tts.factory import create_tts_backend
        from artificial_u.services.tts_service import TTSService

        backend = create_tts_backend(backend_name=backend_name, logger=self.logger)

        tts_service = TTSService(
            backend=backend,
            repository_factory=self.repository_factory,
            logger=self.logger,
        )
        try:
            audio_bytes = tts_service.generate_lecture_audio(
                lecture=lecture,
                professor=professor,
                voice_id=el_voice_id,
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

    def _add_id3_tags_to_audio(
        self, lecture, course, topic, audio_bytes: bytes, tts_backend: str = "elevenlabs"
    ) -> bytes:
        """Add ID3 metadata tags to audio bytes."""
        from artificial_u.audio import ID3Tagger
        from artificial_u.config import get_settings

        try:
            tagger = ID3Tagger(logger=self.logger)

            # Calculate track number based on topic position
            track_number = tagger.calculate_track_number(
                topic_week=topic.week,
                topic_order=topic.order,
                course_id=course.id,
                repository_factory=self.repository_factory,
            )

            # Generate comment with model and TTS backend info
            settings = get_settings()
            model_name = getattr(lecture, "created_with", None) or settings.TTS_VOICE_MODEL
            comment = tagger.generate_comment(
                model_name=model_name,
                tts_backend=tts_backend,
            )

            # Add tags to audio
            tagged_audio = tagger.add_tags_to_audio(
                audio_bytes=audio_bytes,
                title=lecture.title or f"Lecture {topic.week}.{topic.order}",
                album=course.title,
                track_number=track_number,
                year=lecture.created_at.year if hasattr(lecture, "created_at") else None,
                comment=comment if comment else None,
            )

            return tagged_audio

        except Exception as e:
            self.logger.warning(
                f"Failed to add ID3 tags to audio, using untagged version: {e}",
                exc_info=True,
            )
            # If tagging fails, return original audio bytes
            return audio_bytes
