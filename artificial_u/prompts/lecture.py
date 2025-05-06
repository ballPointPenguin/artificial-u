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
LECTURE_XML_STRUCTURE = """<lecture>
  <content>
    [Full lecture content, including:
    - Title or Topic
    - Introduction and scene setting
    - Main points and explanations
    - Student interactions and questions
    - Examples and analogies
    - Stage directions in [brackets]
    - Natural transitions between topics
    - Conclusion and preview of next lecture]
  </content>
</lecture>"""

# Example of a filled lecture
EXAMPLE_LECTURE_1 = """<lecture>
  <content>
    Introduction to Quantum Computing

    [Professor enters, adjusting her glasses with a smile]

    Good morning, everyone! I'm Dr. Sarah Chen, and I'm thrilled to begin our journey into the
    fascinating world of quantum computing. Before we dive in, let me share a story that I think
    perfectly illustrates why this field is so exciting...

    [Walks to the whiteboard, drawing a simple diagram]

    You see, classical computers, the ones we use every day, are like trying to read a book in a
    dark room with just one flashlight. You can only see one page at a time. But quantum computers?
    They're like suddenly turning on all the lights in the room. You can see every page at once!

    [Pauses, looking around the room]

    I see some skeptical faces. Good! That skepticism is exactly where we need to begin. Let's break
    this down into something more tangible...

    [Continues with main lecture content, including student interactions, examples, and transitions]

    And that brings us to our conclusion for today. Next time, we'll build on these foundational
    concepts to explore quantum superposition in more detail. Any final questions?
  </content>
</lecture>"""

# Example of a filled lecture with different style
EXAMPLE_LECTURE_2 = """<lecture>
  <content>
    The French Revolution: Causes and Catalysts

    [Professor strides in, carrying a worn leather briefcase]

    Bonjour, class! Professor Martin here. Today we begin our exploration of one of history's most
    pivotal moments - the French Revolution. But before we discuss the storming of the Bastille or
    the Reign of Terror, we need to understand why France was ripe for revolution in the first
    place.

    [Opens briefcase, pulls out a replica of an 18th-century French coin]

    Take a look at this. This simple coin tells us so much about pre-revolutionary France...

    [Passes coin around while continuing lecture]

    The story of the French Revolution is not just about kings and queens, but about ordinary people
    facing extraordinary circumstances. Let's examine the three estates system...

    [Continues with engaging narrative, weaving together social, economic, and political factors]

    Next time, we'll see how these tensions finally boiled over in 1789. Remember, revolutions don't
    just happen - they brew over time, like a pot slowly coming to boil.
  </content>
</lecture>"""

# Unified lecture prompt that handles both structured and freeform inputs
LECTURE_PROMPT = PromptTemplate(
    template=f"""
Generate a university lecture in XML format.
Use the structure below; fill in the <content></content> tags with the lecture content.

XML Structure:
{LECTURE_XML_STRUCTURE}

Course Information:
{{course_xml}}

Professor Information:
{{professor_xml}}

Topic for this lecture:
{{topic_xml}}

Summary of existing lectures in this course (for context and continuity):
{{existing_lectures_xml}}

List of topics in this course (for context and continuity):
{{topics_xml}}

{{freeform_prompt_text}}

Examples of properly formatted lectures:
Example 1:
{EXAMPLE_LECTURE_1}

Example 2:
{EXAMPLE_LECTURE_2}

IMPORTANT:
- Write in a conversational style that matches the professor's personality
- Include stage directions in [brackets] to bring the scene to life
- Avoid complex mathematical formulas - express them in spoken language
- Create a narrative flow rather than just presenting facts
- Include natural interactions and engagement
- Produce text content that is suitable for a text-to-speech engine
- Aim for approximately {{word_count}} words in the lecture content

Wrap your answer in <output> tags, providing only the <lecture> element.
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
    word_count: int = 2500,
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
