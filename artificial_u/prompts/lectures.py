"""Lecture-related prompt templates."""

from typing import Optional
from artificial_u.prompts.base import PromptTemplate, StructuredPrompt, xml_tag

# Basic lecture generation template
LECTURE_PROMPT = PromptTemplate(
    template="""You are an AI assistant tasked with generating engaging university lecture texts for various courses. These lectures will be used in a text-to-speech engine, so it's crucial to create content that works well in spoken form. Your goal is to produce a lecture that is approximately {word_count} words long, narrative in style, and infused with the personality of the lecturer.

Course: {course_title} ({course_code})
Lecture Topic: {topic}
Week: {week_number}, Lecture: {order_in_week}

Professor Details:
- Name: {professor_name}
- Background: {professor_background}
- Teaching Style: {teaching_style}
- Personality: {professor_personality}

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
[Your detailed lecture plan here]
</lecture_preparation>

<lecture_text>
[The complete lecture text here, ready for text-to-speech]
</lecture_text>""",
    required_vars=[
        "course_title",
        "course_code",
        "topic",
        "week_number",
        "order_in_week",
        "professor_name",
        "professor_background",
        "teaching_style",
        "professor_personality",
        "word_count",
    ],
)


# Structured version of the lecture prompt for more flexibility
class StructuredLecturePrompt(StructuredPrompt):
    """A structured prompt for generating lectures with configurable sections."""

    def __init__(self, word_count: int = 2500):
        """Initialize a structured lecture prompt.

        Args:
            word_count: Target word count for the lecture
        """
        super().__init__()

        # Add default sections
        self.add_section(
            "introduction",
            """You are an AI assistant tasked with generating engaging university lecture texts for various courses. These lectures will be used in a text-to-speech engine, so it's crucial to create content that works well in spoken form. Your goal is to produce a lecture that is approximately {word_count} words long, narrative in style, and infused with the personality of the lecturer.""",
        )

        self.add_section(
            "course_info",
            """Course: {course_title} ({course_code})
Lecture Topic: {topic}
Week: {week_number}, Lecture: {order_in_week}""",
        )

        self.add_section(
            "professor_info",
            """Professor Details:
- Name: {professor_name}
- Background: {professor_background}
- Teaching Style: {teaching_style}
- Personality: {professor_personality}""",
        )

        self.add_section("continuity", "{continuity_context}")

        self.add_section(
            "preparation_instructions",
            """Before writing the lecture, please plan your approach inside <lecture_preparation> tags. In your preparation:

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
   - Consider places for student interaction""",
        )

        self.add_section(
            "writing_instructions",
            """After your preparation, write the lecture as a continuous text, following these guidelines:

1. Begin with a vivid introduction that sets the scene and introduces the lecturer
2. Write in a conversational, engaging style that reflects the lecturer's personality
3. Avoid complex mathematical formulas - express them in spoken language
4. Include stage directions in [brackets] to bring the scene to life
5. Focus on creating a narrative flow rather than presenting dry facts
6. Aim for approximately {word_count} words in length""",
        )

        self.add_section(
            "output_format",
            """Your output should follow this structure:

<lecture_preparation>
[Your detailed lecture plan here]
</lecture_preparation>

<lecture_text>
[The complete lecture text here, ready for text-to-speech]
</lecture_text>""",
        )

        # Store word count
        self.word_count = word_count

    def format(self, **kwargs) -> str:
        """Format the prompt with the provided variables."""
        # Ensure word count is included
        if "word_count" not in kwargs:
            kwargs["word_count"] = self.word_count

        # Format continuity context if provided
        if "previous_lecture_content" in kwargs and kwargs["previous_lecture_content"]:
            kwargs[
                "continuity_context"
            ] = f"""Previous lecture summary:
{kwargs['previous_lecture_content'][:500]}...

Build on these concepts appropriately."""
        else:
            kwargs["continuity_context"] = ""

        # Format each section
        for name in self.order:
            section = self.sections.get(name)
            if section and section["enabled"]:
                section["content"] = section["content"].format(**kwargs)

        # Render the complete prompt
        return self.render()


def get_lecture_prompt(
    course_title: str,
    course_code: str,
    topic: str,
    week_number: int,
    order_in_week: int,
    professor_name: str,
    professor_background: str,
    teaching_style: str,
    professor_personality: str,
    previous_lecture_content: Optional[str] = None,
    word_count: int = 2500,
) -> str:
    """Generate a lecture prompt.

    Args:
        course_title: Course title
        course_code: Course code
        topic: Lecture topic
        week_number: Week number in the course
        order_in_week: Order of this lecture within the week
        professor_name: Name of the professor
        professor_background: Background of the professor
        teaching_style: Professor's teaching style
        professor_personality: Professor's personality traits
        previous_lecture_content: Optional content from previous lecture for continuity
        word_count: Word count for the lecture

    Returns:
        str: Formatted lecture prompt
    """
    # Format continuity context if provided
    continuity_context = ""
    if previous_lecture_content:
        continuity_context = f"""<previous_lecture>
{previous_lecture_content[:500]}...
</previous_lecture>

Build on these concepts appropriately."""

    return LECTURE_PROMPT(
        course_title=course_title,
        course_code=course_code,
        topic=topic,
        week_number=week_number,
        order_in_week=order_in_week,
        professor_name=professor_name,
        professor_background=professor_background,
        teaching_style=teaching_style,
        professor_personality=professor_personality,
        continuity_context=continuity_context,
        word_count=word_count,
    )


def get_structured_xml_lecture_prompt(
    course_title: str,
    course_code: str,
    topic: str,
    week_number: int,
    order_in_week: int,
    professor_name: str,
    professor_title: str,
    professor_background: str,
    teaching_style: str,
    professor_personality: str,
    previous_lecture_content: Optional[str] = None,
    word_count: int = 2500,
) -> str:
    """Generate a lecture prompt with enhanced XML structure.

    This version uses a clearer XML tag structure with distinct sections
    for instructions, course info, professor profile, and output format.

    Args:
        course_title: Course title
        course_code: Course code
        topic: Lecture topic
        week_number: Week number in the course
        order_in_week: Order of this lecture within the week
        professor_name: Name of the professor
        professor_title: Academic title of the professor
        professor_background: Background of the professor
        teaching_style: Professor's teaching style
        professor_personality: Professor's personality traits
        previous_lecture_content: Optional content from previous lecture for continuity
        word_count: Word count for the lecture

    Returns:
        str: Formatted lecture prompt with XML structure
    """
    # Format continuity context if provided
    continuity_context = ""
    if previous_lecture_content:
        continuity_context = f"""<previous_lecture>
{previous_lecture_content[:500]}...
</previous_lecture>

Build on these concepts appropriately."""

    prompt = f"""<instructions>
You are creating an engaging university lecture for a course.
The lecture should be approximately {word_count} words long, narrative in style,
and infused with the personality of the lecturer.
</instructions>

<course_info>
Course: {course_title} ({course_code})
Department: {course_title.split(':')[0] if ':' in course_title else course_code[:2]}
Lecture Topic: {topic}
Week: {week_number}, Lecture: {order_in_week}
</course_info>

<professor_profile>
Name: {professor_name}
Title: {professor_title}
Background: {professor_background}
Teaching Style: {teaching_style}
Personality: {professor_personality}
</professor_profile>

{continuity_context}

<output_instructions>
1. First, develop a lecture preparation plan in <lecture_preparation></lecture_preparation> tags
2. Then write the full lecture in <lecture_text></lecture_text> tags, following these guidelines:
   - Begin with a vivid introduction that sets the scene
   - Write in a conversational style reflecting the professor's personality
   - Avoid complex mathematical formulas - express them in spoken language
   - Include stage directions in [brackets] to bring the scene to life
   - Focus on creating a narrative flow rather than presenting dry facts
   - Aim for approximately {word_count} words in length
</output_instructions>"""

    return prompt
