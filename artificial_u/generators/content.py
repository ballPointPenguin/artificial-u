"""
Content generator for ArtificialU using either Anthropic Claude API or alternative models.
"""

import os
from typing import Dict, List, Optional, Any
import anthropic
import json
import re

from artificial_u.models.core import Professor, Course, Lecture


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
        prompt = f"""Create a detailed profile for a professor in the {department} department, specializing in {specialization}.

{f"Gender: {gender}" if gender else ""}
{f"Nationality/cultural background: {nationality}" if nationality else ""}
{f"Age range: {age_range}" if age_range else ""}

Create a rich, realistic faculty profile with the following structure:

<professor_profile>
Name: [Full name with title]
Title: [Academic title]
Background: [Educational and professional background]
Personality: [Personality traits evident in teaching]
Teaching Style: [Distinctive teaching approach]
</professor_profile>

Make this professor feel like a real person with depth. Include educational background, personality traits that show in teaching, and a distinctive teaching style."""

        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2000,
            temperature=1,
            system="You are an expert at creating rich, realistic faculty profiles for an educational content system.",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        # Extract the profile content
        content = response.content[0].text
        profile_match = re.search(
            r"<professor_profile>\s*(.*?)\s*</professor_profile>", content, re.DOTALL
        )
        if not profile_match:
            raise ValueError("No professor profile found in response")

        profile_text = profile_match.group(1).strip()

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
        prompt = f"""Create a detailed course syllabus for {course.code}: {course.title}

Course Information:
- Department: {course.department}
- Professor: {professor.name} ({professor.title})
- Teaching Style: {professor.teaching_style}

Create a comprehensive syllabus with the following structure:

<syllabus>
Course Description: [Overview of the course and its objectives]

Learning Outcomes:
[List of 4-6 specific outcomes students will achieve]

Course Structure:
[Weekly breakdown of topics and activities]

Assessment Methods:
[Description of how students will be evaluated]

Required Materials:
[List of necessary textbooks, resources, or materials]

Course Policies:
[Key policies on attendance, participation, and academic integrity]
</syllabus>

Make this syllabus clear, professional, and aligned with the professor's teaching style."""

        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=3000,
            temperature=0.7,
            system="You are an expert at creating detailed, professional course syllabi that align with academic standards.",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        # Extract the syllabus content
        content = response.content[0].text
        syllabus_match = re.search(
            r"<syllabus>\s*(.*?)\s*</syllabus>", content, re.DOTALL
        )

        if syllabus_match:
            # If we find the tags, use the content inside them
            return syllabus_match.group(1).strip()
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
        continuity_context = ""
        if previous_lecture_content:
            continuity_context = f"""Previous lecture summary:
{previous_lecture_content[:500]}...

Build on these concepts appropriately."""

        prompt = f"""You are an AI assistant tasked with generating engaging university lecture texts for various courses. These lectures will be used in a text-to-speech engine, so it's crucial to create content that works well in spoken form. Your goal is to produce a lecture that is approximately {word_count} words long, narrative in style, and infused with the personality of the lecturer.

Course: {course.title} ({course.code})
Lecture Topic: {topic}
Week: {week_number}, Lecture: {order_in_week}

Professor Details:
- Name: {professor.name}
- Background: {professor.background}
- Teaching Style: {professor.teaching_style}
- Personality: {professor.personality}

{continuity_context}

Before writing the lecture, please plan your approach inside <lecture_preparation> tags. In your preparation:

1. Consider how to structure the lecture for optimal audio delivery:
   - Plan clear transitions between main points
   - Note places where pauses or changes in tone might be effective
   - Consider how to naturally incorporate student interactions

2. Outline 5-7 main points for the lecture:
   - For each point, note key information to cover
   - Consider how each point builds on the previous one
   - Break down technical concepts into simpler components
   - Prepare analogies or real-world examples

3. Plan the pacing of the lecture:
   - Estimate how long to spend on each main point
   - Note where to place breaks or moments of levity
   - Consider places for student interaction

After your preparation, write the lecture as a continuous text, following these guidelines:

1. Begin with a vivid introduction that sets the scene and introduces the lecturer
2. Write in a conversational, engaging style that reflects the lecturer's personality
3. Avoid complex mathematical formulas - express them in spoken language
4. Include stage directions in [brackets] to bring the scene to life
5. Focus on creating a narrative flow rather than presenting dry facts
6. Aim for approximately {word_count} words in length

Your output should follow this structure:

<lecture_preparation>
[Your detailed lecture preparation goes here]
</lecture_preparation>

<lecture>
[The full lecture text, including introduction and stage directions]
</lecture>"""

        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=20000,
            temperature=1,
            system="You are an expert at creating engaging, realistic university lectures that capture the personality and teaching style of specific professors.",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )

        # Extract the lecture content from between the <lecture> tags
        content = response.content[0].text
        lecture_match = re.search(r"<lecture>\s*(.*?)\s*</lecture>", content, re.DOTALL)
        if not lecture_match:
            raise ValueError("No lecture content found in response")

        lecture_content = lecture_match.group(1).strip()

        # Try to extract a title from the first line
        title = topic
        first_line = lecture_content.split("\n")[0].strip("# []")
        if (
            first_line and len(first_line) < 100
        ):  # Use first line if it looks like a title
            title = first_line

        return Lecture(
            title=title,
            course_id=course.id or course.code,
            week_number=week_number,
            order_in_week=order_in_week,
            description=f"Week {week_number}, Lecture {order_in_week}: {topic}",
            content=lecture_content,
        )
