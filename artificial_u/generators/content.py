"""
Content generator for ArtificialU using either Anthropic Claude API or alternative models.
"""

import os
from typing import Dict, List, Optional, Any
import anthropic
import json
import re

from artificial_u.models.core import Professor, Course, Lecture
from artificial_u.prompts.professors import get_professor_prompt
from artificial_u.prompts.courses import get_syllabus_prompt
from artificial_u.prompts.lectures import get_lecture_prompt
from artificial_u.prompts.system import get_system_prompt
from artificial_u.prompts.base import extract_xml_content


class ContentGenerator:
    """
    Generates academic content using the Anthropic Claude API or alternative models.
    """

    def __init__(self, api_key: Optional[str] = None, client: Optional[Any] = None):
        """
        Initialize the content generator.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY environment variable.
            client: Optional pre-configured client (for testing or alternative models)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

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
    ) -> Professor:
        """
        Generate a professor profile with a consistent personality and background.

        Args:
            department: Academic department
            specialization: Area of expertise
            gender: Optional gender specification
            nationality: Optional nationality specification
            age_range: Optional age range (e.g., "30-40", "50-60")

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
        )

        # Get the system prompt
        system_prompt = get_system_prompt("professor")

        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2000,
            temperature=1,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        # Extract the profile content
        content = response.content[0].text
        profile_text = extract_xml_content(content, "professor_profile")

        if not profile_text:
            raise ValueError("No professor profile found in response")

        # Parse the profile text into a dictionary
        profile = {}
        for line in profile_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                profile[key.strip()] = value.strip()

        return Professor(
            name=profile.get("Name", ""),
            title=profile.get("Title", ""),
            department=department,
            specialization=specialization,
            background=profile.get("Background", ""),
            personality=profile.get("Personality", ""),
            teaching_style=profile.get("Teaching Style", ""),
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
            model="claude-3-7-sonnet-20250219",
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
            model="claude-3-7-sonnet-20250219",
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
