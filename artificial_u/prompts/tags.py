from typing import Any, Dict, List, Optional

from artificial_u.models.converters import partial_course_to_xml
from artificial_u.prompts.base import PromptTemplate

TAGS_XML_STRUCTURE = """<tags>
  <tag>[Tag name]</tag>
  <tag>[Another tag name]</tag>
</tags>"""

EXAMPLE_TAGS = """<tags>
  <tag>Philosophy of Mind</tag>
  <tag>Consciousness</tag>
  <tag>Cognitive Science</tag>
  <tag>Neuroscience</tag>
</tags>"""

# Cap syllabus context so long courses don't blow up the prompt
MAX_TOPIC_TITLES = 30

COURSE_TAGS_PROMPT = PromptTemplate(
    template=f"""
Generate subject tags for the university course described below.

Rules:
- Return between 3 and 7 `<tag>` elements.
- Each tag is a short noun phrase in Title Case, one to three words, in English.
- Tags describe what the course is about: subject areas, themes, and methods.
  A tag for the level or character of the course (e.g. "Introductory", "Hands-On")
  is welcome when it is distinctive.
- STRONGLY prefer reusing tags from the existing vocabulary when one fits;
  invent a new tag only when nothing in the vocabulary applies.
- Do not simply restate the department name; tags should add information
  beyond the department.
- No duplicates or near-duplicates (e.g. do not return both "Ethics" and "Ethical").
- Escape XML-sensitive characters inside text nodes, especially `&`, `<`, and `>`.

Required XML structure:
{TAGS_XML_STRUCTURE}

Course information:
{{course_xml}}
{{department_context}}{{topics_context}}{{vocabulary_context}}
Example of properly formatted output:
{EXAMPLE_TAGS}

Wrap your answer in <output> tags, providing only the single <tags> element.
""",
    required_vars=[
        "course_xml",
        "department_context",
        "topics_context",
        "vocabulary_context",
    ],
)


def get_course_tags_prompt(
    course_data: Dict[str, Any],
    *,
    department_name: Optional[str] = None,
    topic_titles: Optional[List[str]] = None,
    existing_tags: Optional[List[str]] = None,
) -> str:
    """Generate the prompt for tagging a course.

    Args:
        course_data: Course attributes (code, title, description, level, ...)
        department_name: Name of the department offering the course
        topic_titles: Topic titles from the course syllabus
        existing_tags: Current tag vocabulary to prefer, most-used first
    """
    course_xml_str = partial_course_to_xml(course_data)

    department_context = f"Department: {department_name}\n" if department_name else ""

    topics_context = ""
    if topic_titles:
        titles = "\n".join(f"- {title}" for title in topic_titles[:MAX_TOPIC_TITLES])
        topics_context = f"Topic titles from the course syllabus:\n{titles}\n"

    vocabulary_context = ""
    if existing_tags:
        vocabulary = "\n".join(f"- {name}" for name in existing_tags)
        vocabulary_context = (
            f"Existing tag vocabulary (most-used first, prefer reusing these):\n{vocabulary}\n"
        )

    try:
        return COURSE_TAGS_PROMPT.format(
            course_xml=course_xml_str,
            department_context=department_context,
            topics_context=topics_context,
            vocabulary_context=vocabulary_context,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting COURSE_TAGS_PROMPT: {e}")
