"""Lecture-related prompt templates."""

from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    lectures_to_xml,
    partial_course_to_xml,
    professor_to_xml,
    topic_to_xml,
    topics_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

# XML structure for lecture content
LECTURE_XML_STRUCTURE = """
<lecture>
  <title>
    [Title of the lecture]
  </title>
  <content>
    [Full lecture content]
  </content>
</lecture>
"""

# Unified lecture prompt that handles both structured and freeform inputs
LECTURE_PROMPT = PromptTemplate(
    template=f"""
{{course_xml}}

{{professor_xml}}

{{topic_xml}}

{{existing_lectures_xml}}

{{topics_xml}}

{{freeform_prompt_text}}

Instructions:

1. Review the provided information carefully to understand the context of the lecture.

2. Generate a lecture that is approximately {{word_count}} words long, suitable for audio delivery.

3. Structure your response in the following XML format:

{LECTURE_XML_STRUCTURE}

4. In the <content> section, include the following elements:
   - Title or Topic (repeated from the <title> section)
   - Introduction and scene setting
   - Main points and explanations
   - Student interactions and questions (optional)
   - Examples and analogies
   - Stage directions in [brackets]
   - Natural transitions between topics
   - Conclusion and preview of next lecture

5. Write in a conversational style that matches the professor's personality
   as described in the professor information.

6. Avoid complex mathematical formulas -
   express them in spoken language suitable for audio delivery.

7. Create a narrative flow rather than just presenting facts.

8. Include natural interactions and engagement with the audience.

9. Ensure that the text is suitable for a text-to-speech engine:
   - Avoid superfluous punctuation such as asterisks or dashes.
   - Everything in the response text will be literally read aloud.

Before writing the final lecture, outline the structure and main points of your lecture
inside <lecture_outline> tags. This will help ensure a well-organized and coherent presentation.
In this outline:

- List out the main topics and subtopics for the lecture.
- Provide a brief description of how each topic relates to the course and previous lectures.
- Suggest potential examples, analogies, or student interactions for each main topic.

It's OK for this section to be quite long, as it will help in creating a
comprehensive and engaging lecture.

Remember to imbue the text with the personality of the professor while maintaining
the required structure and content.
""",
    required_vars=[
        "course_xml",
        "professor_xml",
        "topic_xml",
        "existing_lectures_xml",
        "topics_xml",
        "freeform_prompt_text",
        "word_count",
    ],
)


def get_lecture_prompt(
    course_data: Dict[str, Any],
    professor_data: Dict[str, Any],
    topic_data: Dict[str, Any],
    existing_lectures: List[Dict[str, Any]],
    topics_data: List[Dict[str, Any]],
    freeform_prompt: Optional[str] = None,
    word_count: int = 3000,
) -> str:
    """Generate a lecture prompt using centralized converters.

    Args:
        course_data: Dictionary of course attributes
        professor_data: Dictionary of professor attributes
        topic_data: Dictionary of topic attributes
        existing_lectures: List of existing lecture attribute dictionaries
        topics_data: List of topic attribute dictionaries
        freeform_prompt: Optional freeform text context
        word_count: Target word count for the lecture

    Returns:
        Formatted prompt string
    """
    # Use converters to generate XML sections
    course_xml_str = partial_course_to_xml(course_data)
    professor_xml_str = professor_to_xml(professor_data)
    topic_xml_str = topic_to_xml(topic_data)
    existing_lectures_xml_str = lectures_to_xml(existing_lectures)
    topics_xml_str = topics_to_xml(topics_data)

    # Format freeform prompt if provided
    freeform_prompt_text = (
        f"Additional context/ideas for the lecture:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    # Format the main prompt template
    try:
        return LECTURE_PROMPT.format(
            course_xml=course_xml_str,
            professor_xml=professor_xml_str,
            topic_xml=topic_xml_str,
            existing_lectures_xml=existing_lectures_xml_str,
            topics_xml=topics_xml_str,
            word_count=word_count,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting LECTURE_PROMPT: {e}")
