"""Course-related prompt templates."""

from typing import Any, Dict, List, Optional

# Import converters instead of defining formatters here
from artificial_u.models.converters import (
    connected_courses_to_xml,
    courses_to_xml,
    department_to_xml,
    partial_course_to_xml,
    professor_to_xml,
    topics_to_xml,
)
from artificial_u.prompts.base import PromptTemplate

# XML structure for course + weekly syllabus topics
COURSE_XML_STRUCTURE = """<course>
  <code>[Course code]</code>
  <title>[Course title]</title>
  <description>[Course description]</description>
  <level>[Course level: "Undergraduate" or "Graduate"]</level>
  <lectures_per_week>[Course lectures per week]</lectures_per_week>
  <total_weeks>[Course total weeks]</total_weeks>
  <notes>[Optional pedagogical, delivery, or language directive; omit or leave empty]</notes>
  <topics>
    <topic>
      <title>[Weekly theme or topic title]</title>
      <week>[Week number]</week>
      <order>[Order in week]</order>
      <content>
        <lecture>[Sharp, evocative lecture title or conceptual description]</lecture>
        <readings>
          <reading>[Foundational book, article, essay, or primary work]</reading>
          <reading>[Reading 2]</reading>
        </readings>
        <objectives>
          <objective>[Learning objective 1]</objective>
          <objective>[Learning objective 2]</objective>
        </objectives>
      </content>
    </topic>
  </topics>
</course>"""

# Example courses to demonstrate the format
EXAMPLE_COURSE_1 = """<course>
  <code>PHIL215</code>
  <title>Philosophy of Mind and Consciousness</title>
  <description>An inquiry into the nature of mentality, subjective experience, personal identity,
  and artificial intelligence, tracing debates from Cartesian dualism to contemporary cognitive
  science.</description>
  <level>Undergraduate</level>
  <lectures_per_week>1</lectures_per_week>
  <total_weeks>4</total_weeks>
  <topics>
    <topic>
      <title>The "Hard Problem" of Consciousness</title>
      <week>1</week>
      <order>1</order>
      <content>
        <lecture>What Is It Like to Be a Bat? Defining Subjective Experience</lecture>
        <readings>
          <reading>Nagel, Thomas. "What Is It Like to Be a Bat?"</reading>
          <reading>Chalmers, David. "Facing Up to the Problem of Consciousness."</reading>
        </readings>
        <objectives>
          <objective>Distinguish phenomenal consciousness from functional explanation</objective>
        </objectives>
      </content>
    </topic>
    <topic>
      <title>Physicalism and Qualia</title>
      <week>2</week>
      <order>1</order>
      <content>
        <lecture>Mary's Room and the Knowledge Argument</lecture>
        <readings>
          <reading>Jackson, Frank. "Epiphenomenal Qualia."</reading>
          <reading>Dennett, Daniel. Consciousness Explained (selections).</reading>
        </readings>
        <objectives>
          <objective>Evaluate physicalist responses to the knowledge argument</objective>
        </objectives>
      </content>
    </topic>
  </topics>
</course>"""

# Unified course + syllabus prompt that handles both initial generation and iterative refinement
COURSE_PROMPT = PromptTemplate(
    template=f"""
Generate a complete, intellectually grounded university course and week-by-week syllabus in XML format,
turning broad subjects, freeform brainstorming ideas, or references to specific scholars, writers,
and thinkers into a cohesive curriculum.

XML Structure:
{COURSE_XML_STRUCTURE}

Steps & Guidelines:
1. Frame the Course Identity:
   - `<code>` & `<title>`: Create an appropriate academic course code and an engaging, academically
     resonant course title.
   - `<description>`: Write a concise, catalog-style description synthesizing the intellectual scope
     and central inquiry of the course.
   - `<level>`: Choose either "Undergraduate" or "Graduate" based on complexity and target audience.
   - `<total_weeks>` & `<lectures_per_week>`:
     - Default to 10-12 weeks and 1 core topic per week, or expand to 2 topics per week when the
       scope is broad or interdisciplinary (maximum 3 lectures per week).
     - Respect any explicit values requested by the user.
   - `<notes>` (optional):
     - Omit `<notes>` or leave it empty by default. Do NOT copy the user's raw brainstorming prompt
       or repeat the course description here.
     - Only populate `<notes>` with a concise, clean directive if the user's prompt contains a
       standing pedagogical, format, tone, or language constraint that downstream lecture writers
       must know across every lecture (e.g., "Despite being a math course, avoid heavy symbolic
       formulas and focus on audio-friendly narrative philosophical math" or "This is a French
       course taught to English speakers; deliver lectures primarily in English while introducing
       French concepts and examples"). If `<user_notes>` are already present in Partial Course
       Details, preserve or refine them.

2. Design the Week-by-Week Curriculum (`<topics>`):
   - Organize the subject matter into a logical progression of weekly `<topic>` modules covering
     every slot from week 1 to `total_weeks` and order 1 to `lectures_per_week` within each week
     (`total_weeks * lectures_per_week` total `<topic>` elements).
   - `<title>`: Assign a clear conceptual theme or topic title to each slot that builds toward the
     course's overarching inquiry.
   - `<content>`:
     - `<lecture>`: Include a sharp, evocative lecture title or conceptual focus.
     - `<readings>`: Pair each topic with curated reading suggestions (foundational books, articles,
       essays, or primary works by relevant scholars, writers, and thinkers).
     - `<objectives>` (optional) and `<notes>` (optional): Key learning objectives or context.

3. Tone and Guardrails:
   - Academic and Succinct: Write in an informative, scholarly, and concise voice that prioritizes
     conceptual structure and intellectual connections over fluff.
   - Content Over Logistics: Focus strictly on intellectual architecture (themes, lectures, and
     readings). Do not include administrative boilerplate (grading rubrics, attendance policies,
     office hours) or filler "course review/wrap-up" weeks unless a substantive capstone is warranted.
   - Escape XML-sensitive characters inside text nodes, especially `&` (`&amp;`), `<` (`&lt;`), and `>` (`&gt;`).
   - If a current syllabus draft is provided below alongside new instructions in the user prompt,
     treat the existing course details and topics as a working draft and revise any course fields
     (`title`, `code`, `description`, `level`, `lectures_per_week`, `total_weeks`) and `<topics>`
     needed to fulfill the user's requested changes while keeping the curriculum cohesive.

Existing courses (for context and to avoid repetition):
{{existing_courses_xml}}

Connected courses (explicitly linked prerequisites or sequence partners — align with these):
{{connected_courses_xml}}
{{related_courses_topics_context}}
Department Information:
{{department_xml}}

Professor Information:
{{professor_xml}}

Partial Course Details:
{{partial_course_xml}}
{{existing_topics_context}}
{{freeform_prompt_text}}

Example of a properly formatted course syllabus (abbreviated to 2 weeks for illustration):
{EXAMPLE_COURSE_1}

Wrap your answer in <output> tags, providing only the <course> element (including its nested <topics>).
""",
    required_vars=[
        "existing_courses_xml",
        "connected_courses_xml",
        "related_courses_topics_context",
        "department_xml",
        "professor_xml",
        "partial_course_xml",
        "existing_topics_context",
        "freeform_prompt_text",
    ],
)


def get_course_prompt(
    existing_courses: List[Dict[str, Any]],
    department_data: Dict[str, Any],
    professor_data: Dict[str, Any],
    partial_course_attrs: Dict[str, Any],
    freeform_prompt: Optional[str] = None,
    connected_courses: Optional[List[Dict[str, Any]]] = None,
    existing_topics: Optional[List[Dict[str, Any]]] = None,
    related_courses_topics_context: Optional[str] = None,
) -> str:
    """Generate a course + syllabus prompt using centralized converters.

    Args:
        existing_courses: List of existing course attribute dictionaries.
        department_data: Dictionary of department attributes.
        professor_data: Dictionary of professor attributes.
        partial_course_attrs: Dictionary of known/partial course attributes.
        freeform_prompt: Optional freeform text context or refinement instructions.
        connected_courses: Courses explicitly linked for sequence/continuity context.
        existing_topics: Optional list of current draft topics when refining a syllabus draft.
        related_courses_topics_context: Optional formatted topics from connected courses.

    Returns:
        Formatted prompt string.
    """
    # Use converters to generate XML sections
    existing_courses_xml_str = courses_to_xml(existing_courses)
    connected_courses_xml_str = connected_courses_to_xml(connected_courses or [])
    department_xml_str = department_to_xml(department_data, missing_marker="[unspecified]")
    professor_xml_str = professor_to_xml(professor_data, missing_marker="[unspecified]")
    partial_course_xml_str = partial_course_to_xml(partial_course_attrs)

    topics_list = existing_topics or partial_course_attrs.get("topics")
    existing_topics_context = ""
    if topics_list:
        existing_topics_xml = topics_to_xml(topics_list)
        existing_topics_context = (
            "\nCurrent Syllabus Draft Topics (revise and update these along with the course "
            f"details based on the user's instructions):\n{existing_topics_xml}\n"
        )

    related_context = (
        f"\n{related_courses_topics_context}\n" if related_courses_topics_context else ""
    )

    # Format freeform prompt if provided
    freeform_prompt_text = (
        f"User prompt / syllabus instructions:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    # Format the main prompt template
    try:
        return COURSE_PROMPT.format(
            existing_courses_xml=existing_courses_xml_str,
            connected_courses_xml=connected_courses_xml_str,
            related_courses_topics_context=related_context,
            department_xml=department_xml_str,
            professor_xml=professor_xml_str,
            partial_course_xml=partial_course_xml_str,
            existing_topics_context=existing_topics_context,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        # Re-raise or handle missing required variables if COURSE_PROMPT definition changes
        raise ValueError(f"Error formatting COURSE_PROMPT: {e}")
