"""
Content generator for ArtificialU using either Anthropic Claude API or alternative models.
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import anthropic

from artificial_u.models.core import Course, Lecture, Professor
from artificial_u.prompts.base import extract_xml_content
from artificial_u.prompts.courses import get_syllabus_prompt
from artificial_u.prompts.lectures import get_lecture_prompt
from artificial_u.prompts.professors import get_professor_prompt
from artificial_u.prompts.system import get_system_prompt


class ContentGenerator:
    """
    Generates academic content using the Anthropic Claude API or alternative models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[Any] = None,
        enable_caching: bool = False,
        cache_metrics: bool = True,
    ):
        """
        Initialize the content generator.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY environment variable.
            client: Optional pre-configured client (for testing or alternative models)
            enable_caching: Whether to enable prompt caching for supported methods
            cache_metrics: Whether to track cache usage metrics
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.enable_caching = enable_caching
        self.cache_metrics = cache_metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.token_savings = 0

        # Setup logging
        self.logger = logging.getLogger(__name__)

        if client:
            self.client = client
        else:
            if not self.api_key:
                raise ValueError(
                    "Anthropic API key is required when not providing a client"
                )
            self.client = anthropic.Client(api_key=self.api_key)

    def create_professor(
        self,
        department: str,
        specialization: str,
        gender: Optional[str] = None,
        nationality: Optional[str] = None,
        age_range: Optional[str] = None,
        accent: Optional[str] = None,
    ) -> Professor:
        """
        Generate a professor profile with a consistent personality and background.

        Args:
            department: Academic department
            specialization: Area of expertise
            gender: Optional gender specification
            nationality: Optional nationality specification
            age_range: Optional age range (e.g., "30-40", "50-60")
            accent: Optional accent specification

        Returns:
            Professor: Generated professor profile
        """
        # Get the professor prompt using the prompt module
        prompt = get_professor_prompt(
            department=department,
            specialization=specialization,
            gender=gender,
            nationality=nationality,
            age_range=age_range,
            accent=accent,
        )

        # Get the system prompt
        system_prompt = get_system_prompt("professor")

        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            temperature=1,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        # Extract the profile content
        content = response.content[0].text
        profile_text = extract_xml_content(content, "professor_profile")

        if not profile_text:
            # Don't throw error, create a basic professor with required fields
            self.logger.warning(
                "No structured professor profile found. Creating basic profile."
            )

            # Try to extract a name from the content as a fallback
            name_match = re.search(r"Dr\.\s+[\w\s]+|Professor\s+[\w\s]+", content)
            name = (
                name_match.group(0)
                if name_match
                else f"Dr. {specialization.title()} Expert"
            )

            # Create basic professor with required fields and empty optional fields
            return Professor(
                name=name,
                title=f"Professor of {specialization.title()}",
                department=department,
                specialization=specialization,
                background=f"Expert in {specialization} within the {department} department.",
                personality="Professional and knowledgeable.",
                teaching_style="Structured and clear.",
                gender=gender,
                accent=accent,
                description=f"A professor specializing in {specialization}.",
                age=None,
            )

        # Parse the profile text into a dictionary
        profile = {}
        for line in profile_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                profile[key.strip()] = value.strip()

        # Convert age to integer if present
        age = None
        if "Age" in profile:
            try:
                age = int(profile["Age"])
            except ValueError:
                # If age can't be converted to int, leave it as None
                self.logger.warning(
                    f"Could not convert age value to integer: {profile.get('Age')}"
                )

        return Professor(
            name=profile.get("Name", ""),
            title=profile.get("Title", ""),
            department=department,
            specialization=specialization,
            background=profile.get("Background", ""),
            personality=profile.get("Personality", ""),
            teaching_style=profile.get("Teaching Style", ""),
            gender=profile.get("Gender"),
            accent=profile.get("Accent"),
            description=profile.get("Description"),
            age=age,
        )

    def create_course_syllabus(self, course: Course, professor: Professor) -> str:
        """
        Generate a course syllabus based on the course and professor details.

        Args:
            course: Course object with details
            professor: Professor teaching the course

        Returns:
            str: Generated course syllabus
        """
        # Get the syllabus prompt using the prompt module
        prompt = get_syllabus_prompt(
            course_code=course.code,
            course_title=course.title,
            department=course.department,
            professor_name=professor.name,
            professor_title=professor.title,
            teaching_style=professor.teaching_style,
        )

        # Get the system prompt
        system_prompt = get_system_prompt("course")

        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=3000,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        # Extract the syllabus content
        content = response.content[0].text
        syllabus = extract_xml_content(content, "syllabus")

        if syllabus:
            # If we find the tags, use the content inside them
            return syllabus
        elif content.strip():
            # If no tags but content exists, use the whole response
            return content.strip()
        else:
            # Only raise error if truly empty
            raise ValueError("No syllabus found in response")

    def create_lecture(
        self,
        course: Course,
        professor: Professor,
        topic: str,
        week_number: int,
        order_in_week: int,
        previous_lecture_content: Optional[str] = None,
        word_count: int = 2500,
    ) -> Lecture:
        """
        Generate a lecture for a specific course.

        Args:
            course: Course information
            professor: Professor teaching the course
            topic: Lecture topic
            week_number: Week number in the course
            order_in_week: Order of this lecture within the week
            previous_lecture_content: Optional content from previous lecture for continuity
            word_count: Word count for the lecture (default: 2500)

        Returns:
            Lecture: Generated lecture
        """
        # Get the lecture prompt using the prompt module
        prompt = get_lecture_prompt(
            course_title=course.title,
            course_code=course.code,
            topic=topic,
            week_number=week_number,
            order_in_week=order_in_week,
            professor_name=professor.name,
            professor_background=professor.background,
            teaching_style=professor.teaching_style,
            professor_personality=professor.personality,
            previous_lecture_content=previous_lecture_content,
            word_count=word_count,
        )

        # Get the system prompt
        system_prompt = get_system_prompt("lecture")

        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=8000,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        content = response.content[0].text

        # Extract lecture text and preparation from XML tags
        lecture_text = extract_xml_content(content, "lecture_text")
        preparation = extract_xml_content(content, "lecture_preparation")

        # If no XML tags are found, use the whole text as lecture_text
        if not lecture_text:
            if "<lecture_text>" not in content and content.strip():
                lecture_text = content.strip()
            else:
                # For Ollama or other models that might not structure the response with XML tags
                # Extract anything that looks like the main content
                # Look for patterns like paragraph breaks or headers
                lines = content.split("\n")
                if len(lines) > 5:  # If we have a reasonable amount of text
                    lecture_text = content.strip()
                else:
                    raise ValueError("No lecture text found in response")

        # Create a title from the topic, potentially trying to extract a title from the first line
        title = topic
        if lecture_text:
            first_lines = lecture_text.split("\n")[
                :3
            ]  # Check first 3 lines for a good title

            for line in first_lines:
                clean_line = line.strip().strip("# []").strip()
                # Good title criteria: not too short, not too long, doesn't contain common instruction text
                if (
                    len(clean_line) > 5
                    and len(clean_line) < 100
                    and "lecture" not in clean_line.lower()
                    and "text" not in clean_line.lower()
                    and "preparation" not in clean_line.lower()
                    and "plan" not in clean_line.lower()
                ):
                    title = clean_line
                    break

            # If we didn't find a good title in the first lines, use the topic
            if title == topic and topic:
                title = topic

        # Create a description from the topic and course
        description = f"Week {week_number}, Lecture {order_in_week}: {topic}"

        # Create and return the lecture object
        return Lecture(
            title=title,
            course_id=course.id,
            professor_id=professor.id,
            topic=topic,
            week_number=week_number,
            order_in_week=order_in_week,
            description=description,
            content=lecture_text,
            preparation_notes=preparation or "",
        )

    def create_lecture_with_caching(
        self,
        course: Course,
        professor: Professor,
        topic: str,
        week_number: int,
        order_in_week: int,
        previous_lecture_content: Optional[str] = None,
        word_count: int = 2500,
    ) -> Tuple[Lecture, Dict]:
        """
        Generate a lecture for a specific course using prompt caching for consistency
        and reduced token usage. This is especially useful for maintaining the professor's
        voice and teaching style across lectures.

        Args:
            course: Course information
            professor: Professor teaching the course
            topic: Lecture topic
            week_number: Week number in the course
            order_in_week: Order of this lecture within the week
            previous_lecture_content: Optional content from previous lecture for continuity
            word_count: Word count for the lecture (default: 2500)

        Returns:
            Tuple[Lecture, Dict]: Generated lecture and cache metrics
        """
        if not self.enable_caching:
            lecture = self.create_lecture(
                course,
                professor,
                topic,
                week_number,
                order_in_week,
                previous_lecture_content,
                word_count,
            )
            return lecture, {"cached": False, "tokens_saved": 0}

        # Get the system prompt
        system_prompt = get_system_prompt("lecture")

        # Create cached professor and course context
        professor_context = {
            "type": "text",
            "text": f"""<professor_profile>
Name: {professor.name}
Title: {professor.title}
Background: {professor.background}
Teaching Style: {professor.teaching_style}
Personality: {professor.personality}
</professor_profile>""",
            "cache_control": {"type": "ephemeral"},
        }

        course_context = {
            "type": "text",
            "text": f"""<course_info>
Course: {course.title} ({course.code})
Department: {course.department}
Level: {course.level}
Description: {course.description}
</course_info>""",
            "cache_control": {"type": "ephemeral"},
        }

        # Previous lecture context (if available)
        previous_context = None
        if previous_lecture_content:
            previous_context = {
                "type": "text",
                "text": f"""<previous_lecture>
{previous_lecture_content[:1000]}...
</previous_lecture>

Build on these concepts appropriately.""",
                "cache_control": {"type": "ephemeral"},
            }

        # Current lecture request - not cached
        current_request = {
            "type": "text",
            "text": f"""<lecture_request>
Topic: {topic}
Week: {week_number}
Lecture: {order_in_week}
Word Count: {word_count}

Please create a lecture following these guidelines:

1. Begin with a vivid introduction that sets the scene and introduces the lecturer
2. Write in a conversational, engaging style that reflects the professor's personality
3. Avoid complex mathematical formulas - express them in spoken language
4. Include stage directions in [brackets] to bring the scene to life
5. Focus on creating a narrative flow rather than presenting dry facts
6. Aim for approximately {word_count} words in length

Please prepare your lecture and then write it in <lecture_text> tags.
</lecture_request>""",
        }

        # Build the system and messages arrays
        system = [{"type": "text", "text": system_prompt}]

        # Add cacheable elements to system
        system.append(professor_context)
        system.append(course_context)

        if previous_context:
            system.append(previous_context)

        # Create user message
        messages = [{"role": "user", "content": [current_request]}]

        # Track start time for performance measurement
        start_time = time.time()

        # Make API call with caching
        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=8000,
            temperature=0.7,
            system=system,
            messages=messages,
        )

        # Calculate performance metrics
        elapsed = time.time() - start_time

        # Process the response
        content = response.content[0].text

        # Extract lecture text and preparation from XML tags
        lecture_text = extract_xml_content(content, "lecture_text")
        preparation = extract_xml_content(content, "lecture_preparation")

        # If no XML tags are found, use the whole text as lecture_text
        if not lecture_text:
            if "<lecture_text>" not in content and content.strip():
                lecture_text = content.strip()
            else:
                # For Ollama or other models that might not structure the response with XML tags
                # Extract anything that looks like the main content
                # Look for patterns like paragraph breaks or headers
                lines = content.split("\n")
                if len(lines) > 5:  # If we have a reasonable amount of text
                    lecture_text = content.strip()
                else:
                    raise ValueError("No lecture text found in response")

        # Create a title from the topic, potentially trying to extract a title from the first line
        title = topic
        if lecture_text:
            first_lines = lecture_text.split("\n")[
                :3
            ]  # Check first 3 lines for a good title

            for line in first_lines:
                clean_line = line.strip().strip("# []").strip()
                # Good title criteria: not too short, not too long, doesn't contain common instruction text
                if (
                    len(clean_line) > 5
                    and len(clean_line) < 100
                    and "lecture" not in clean_line.lower()
                    and "text" not in clean_line.lower()
                    and "preparation" not in clean_line.lower()
                    and "plan" not in clean_line.lower()
                ):
                    title = clean_line
                    break

            # If we didn't find a good title in the first lines, use the topic
            if title == topic and topic:
                title = topic

        # Create a description from the topic and course
        description = f"Week {week_number}, Lecture {order_in_week}: {topic}"

        # Create and return the lecture object
        lecture = Lecture(
            title=title,
            course_id=course.id,
            professor_id=professor.id,
            topic=topic,
            week_number=week_number,
            order_in_week=order_in_week,
            description=description,
            content=lecture_text,
            preparation_notes=preparation or "",
        )

        # Estimate token savings
        # This is a rough estimate as we don't have exact token counts from the caching
        estimated_context_tokens = (
            len(professor_context["text"] + course_context["text"]) // 4
        )
        if previous_context:
            estimated_context_tokens += len(previous_context["text"]) // 4

        # Track metrics
        cache_info = {
            "cached": True,
            "response_time_seconds": elapsed,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "estimated_tokens_saved": (
                estimated_context_tokens if self.enable_caching else 0
            ),
        }

        if self.cache_metrics:
            self.token_savings += cache_info["estimated_tokens_saved"]
            self.logger.info(
                f"Generated lecture with caching. Estimated tokens saved: {cache_info['estimated_tokens_saved']}"
            )

        return lecture, cache_info

    def create_lecture_series_with_caching(
        self,
        course: Course,
        professor: Professor,
        topics: List[str],
        starting_week: int = 1,
        word_count: int = 2500,
    ) -> List[Tuple[Lecture, Dict]]:
        """
        Generate a series of related lectures using prompt caching for consistency.
        This method maintains professor voice and teaching style across multiple lectures
        and reduces token usage for subsequent lectures in the series.

        Args:
            course: Course object with details
            professor: Professor teaching the course
            topics: List of lecture topics in sequence
            starting_week: Week number to start from (default: 1)
            word_count: Target word count for each lecture (default: 2500)

        Returns:
            List of tuples containing (Lecture, cache_metrics) for each lecture

        Raises:
            ValueError: If topics list is empty
        """
        if not topics:
            raise ValueError("Topics list cannot be empty")

        if not self.enable_caching:
            self.logger.warning(
                "Lecture series caching requested but caching is disabled"
            )
            results = []
            for i, topic in enumerate(topics):
                week_number = starting_week + (i // course.lectures_per_week)
                order_in_week = (i % course.lectures_per_week) + 1

                lecture = self.create_lecture(
                    course=course,
                    professor=professor,
                    topic=topic,
                    week_number=week_number,
                    order_in_week=order_in_week,
                    previous_lecture_content=(
                        results[-1][0].content if results else None
                    ),
                    word_count=word_count,
                )
                results.append((lecture, {"cached": False, "tokens_saved": 0}))
            return results

        # Get the system prompt
        system_prompt = get_system_prompt("lecture")

        # Create cached professor and course context
        professor_context = {
            "type": "text",
            "text": f"""<professor_profile>
Name: {professor.name}
Title: {professor.title}
Background: {professor.background}
Teaching Style: {professor.teaching_style}
Personality: {professor.personality}
</professor_profile>""",
            "cache_control": {"type": "ephemeral"},
        }

        course_context = {
            "type": "text",
            "text": f"""<course_info>
Course: {course.title} ({course.code})
Department: {course.department}
Level: {course.level}
Description: {course.description}
</course_info>""",
            "cache_control": {"type": "ephemeral"},
        }

        # Create base system message array with cacheable elements
        base_system = [
            {"type": "text", "text": system_prompt},
            professor_context,
            course_context,
        ]

        # Results array
        results = []

        # Previous lecture summary for continuity
        previous_lectures_summaries = []

        # Track total tokens saved
        total_tokens_saved = 0

        for i, topic in enumerate(topics):
            week_number = starting_week + (i // course.lectures_per_week)
            order_in_week = (i % course.lectures_per_week) + 1

            # Deep copy the base system messages
            system = base_system.copy()

            # Add previous lecture context if available
            if previous_lectures_summaries:
                previous_context = {
                    "type": "text",
                    "text": f"""<previous_lectures>
{chr(10).join(previous_lectures_summaries[-3:])}
</previous_lectures>

Build on these concepts appropriately.""",
                    "cache_control": {"type": "ephemeral"},
                }
                system.append(previous_context)

            # Current lecture request - not cached
            current_request = {
                "type": "text",
                "text": f"""<lecture_request>
Topic: {topic}
Week: {week_number}
Lecture: {order_in_week}
Word Count: {word_count}

Please create a lecture following these guidelines:

1. Begin with a vivid introduction that sets the scene and introduces the lecturer
2. Write in a conversational, engaging style that reflects the professor's personality
3. Avoid complex mathematical formulas - express them in spoken language
4. Include stage directions in [brackets] to bring the scene to life
5. Focus on creating a narrative flow rather than presenting dry facts
6. Aim for approximately {word_count} words in length

Please prepare your lecture and then write it in <lecture_text> tags.
</lecture_request>""",
            }

            # Create user message
            messages = [{"role": "user", "content": [current_request]}]

            # Track start time for performance measurement
            start_time = time.time()

            # Make API call with caching
            response = self.client.messages.create(
                model="claude-3-7-sonnet-latest",
                max_tokens=8000,
                temperature=0.7,
                system=system,
                messages=messages,
            )

            # Calculate performance metrics
            elapsed = time.time() - start_time

            # Process the response
            content = response.content[0].text

            # Extract lecture text and preparation from XML tags
            lecture_text = extract_xml_content(content, "lecture_text")
            preparation = extract_xml_content(content, "lecture_preparation")

            # If no XML tags are found, use the whole text as lecture_text
            if not lecture_text:
                if "<lecture_text>" not in content and content.strip():
                    lecture_text = content.strip()
                else:
                    # For Ollama or other models that might not structure the response with XML tags
                    # Extract anything that looks like the main content
                    # Look for patterns like paragraph breaks or headers
                    lines = content.split("\n")
                    if len(lines) > 5:  # If we have a reasonable amount of text
                        lecture_text = content.strip()
                    else:
                        raise ValueError(
                            f"No lecture text found in response for topic: {topic}"
                        )

            # Create a title from the topic, potentially trying to extract a title from the first line
            title = topic
            if lecture_text:
                first_lines = lecture_text.split("\n")[
                    :3
                ]  # Check first 3 lines for a good title

                for line in first_lines:
                    clean_line = line.strip().strip("# []").strip()
                    # Good title criteria: not too short, not too long, doesn't contain common instruction text
                    if (
                        len(clean_line) > 5
                        and len(clean_line) < 100
                        and "lecture" not in clean_line.lower()
                        and "text" not in clean_line.lower()
                        and "preparation" not in clean_line.lower()
                        and "plan" not in clean_line.lower()
                    ):
                        title = clean_line
                        break

                # If we didn't find a good title in the first lines, use the topic
                if title == topic and topic:
                    title = topic

            # Create a description from the topic and course
            description = f"Week {week_number}, Lecture {order_in_week}: {topic}"

            # Create and return the lecture object
            lecture = Lecture(
                title=title,
                course_id=course.id,
                professor_id=professor.id,
                topic=topic,
                week_number=week_number,
                order_in_week=order_in_week,
                description=description,
                content=lecture_text,
                preparation_notes=preparation or "",
            )

            # Create a summary for the next lecture
            if lecture_text:
                summary = f"""Lecture {i+1}: {title}
Key points:
- {lecture_text[:300].replace(chr(10), ' ')}...
"""
                previous_lectures_summaries.append(summary)

            # Estimate token savings for this lecture
            estimated_context_tokens = (
                len(professor_context["text"] + course_context["text"]) // 4
            )
            if i > 0 and previous_lectures_summaries:
                estimated_context_tokens += (
                    sum(len(s) for s in previous_lectures_summaries[-3:]) // 4
                )

            # Only count token savings for lectures after the first one
            if i > 0:
                total_tokens_saved += estimated_context_tokens

            # Track metrics for this lecture
            cache_info = {
                "cached": True,
                "lecture_number": i + 1,
                "response_time_seconds": elapsed,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "estimated_tokens_saved": estimated_context_tokens if i > 0 else 0,
                "total_tokens_saved_series": total_tokens_saved,
            }

            if self.cache_metrics:
                self.token_savings += cache_info["estimated_tokens_saved"]
                self.logger.info(
                    f"Generated lecture {i+1}/{len(topics)} with caching. "
                    f"Estimated tokens saved: {cache_info['estimated_tokens_saved']}"
                )

            results.append((lecture, cache_info))

        return results
