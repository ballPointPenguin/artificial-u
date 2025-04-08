"""
Content generator for ArtificialU using the Anthropic Claude API.
"""

import os
from typing import Dict, List, Optional
import anthropic

from artificial_u.models.core import Professor, Course, Lecture


class ContentGenerator:
    """
    Generates academic content using the Anthropic Claude API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the content generator.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

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
        prompt = f"""
        Create a detailed profile for a professor in the {department} department, specializing in {specialization}.
        
        {f"Gender: {gender}" if gender else ""}
        {f"Nationality/cultural background: {nationality}" if nationality else ""}
        {f"Age range: {age_range}" if age_range else ""}
        
        Include:
        1. Full name with appropriate title
        2. Educational and professional background
        3. Personality traits that will be evident in their teaching
        4. Distinctive teaching style
        5. Any unique characteristics or mannerisms
        
        Format the response as a structured profile with clear sections. Make this professor feel like a real person with depth.
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert at creating rich, realistic faculty profiles for an educational content system.",
            messages=[{"role": "user", "content": prompt}],
        )

        # In a real implementation, we would parse the response to extract structured data
        # For now, we'll return a placeholder
        return Professor(
            name="Dr. Example Professor",  # Would be extracted from response
            title="Professor of " + specialization,
            department=department,
            specialization=specialization,
            background="Placeholder background",  # Would be extracted from response
            personality="Placeholder personality",  # Would be extracted from response
            teaching_style="Placeholder teaching style",  # Would be extracted from response
        )

    def create_course_syllabus(self, course: Course, professor: Professor) -> str:
        """
        Generate a complete course syllabus.

        Args:
            course: Course information
            professor: Professor teaching the course

        Returns:
            str: Full course syllabus
        """
        prompt = f"""
        Create a comprehensive syllabus for a {course.level} {course.department} course titled "{course.title}" (Course code: {course.code}).
        
        The course will be taught by {professor.name}, who has the following teaching style and background:
        
        {professor.teaching_style}
        {professor.background}
        
        The course runs for {course.total_weeks} weeks with {course.lectures_per_week} lectures per week.
        
        Include:
        1. Course description
        2. Learning objectives
        3. Weekly schedule with lecture topics
        4. Assessment methods
        5. Required materials
        
        Make sure the content and style reflect both the subject matter and the professor's unique teaching approach.
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=3000,
            temperature=0.5,
            system="You are an expert at creating detailed, realistic course syllabi that reflect both the subject matter and the professor's style.",
            messages=[{"role": "user", "content": prompt}],
        )

        # In a real implementation, we would process the response
        return response.content[0].text

    def create_lecture(
        self,
        course: Course,
        professor: Professor,
        topic: str,
        week_number: int,
        order_in_week: int,
        previous_lecture_content: Optional[str] = None,
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

        Returns:
            Lecture: Generated lecture
        """
        continuity_context = ""
        if previous_lecture_content:
            # Include a brief summary of the previous lecture for continuity
            continuity_context = f"""
            For context, here's a brief summary of the previous lecture:
            {previous_lecture_content[:500]}...
            
            Ensure this lecture builds on these concepts appropriately.
            """

        prompt = f"""
        Create a university lecture on "{topic}" for the course "{course.title}" (Course code: {course.code}).
        
        This is lecture {order_in_week} for week {week_number} of the course.
        
        The lecture should be delivered by {professor.name}, who has the following characteristics:
        - Background: {professor.background}
        - Teaching style: {professor.teaching_style}
        - Personality: {professor.personality}
        
        {continuity_context}
        
        The lecture should:
        1. Be approximately 2000-3000 words
        2. Include clear "stage directions" in [brackets] to indicate the professor's actions, gestures, etc.
        3. Have a conversational, engaging style appropriate for verbal delivery
        4. Include natural pauses, emphasis, and questions that would occur in a real lecture
        5. Reflect the professor's unique personality and teaching approach
        6. Avoid complex mathematical formulas; express mathematical concepts in narrative form
        7. Include realistic interactions with students (e.g., responding to questions)
        
        The lecture should have a clear structure with an introduction, main content, and conclusion.
        """

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=15000,
            temperature=0.7,
            system="You are an expert at creating engaging, realistic university lectures that capture the personality and teaching style of specific professors.",
            messages=[{"role": "user", "content": prompt}],
        )

        lecture_content = response.content[0].text

        return Lecture(
            title=topic,
            course_id=course.id or course.code,
            week_number=week_number,
            order_in_week=order_in_week,
            description=f"Week {week_number}, Lecture {order_in_week}: {topic}",
            content=lecture_content,
        )
