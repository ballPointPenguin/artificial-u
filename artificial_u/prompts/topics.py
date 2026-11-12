from typing import Any, Dict, Optional

from artificial_u.models.converters import partial_course_to_xml
from artificial_u.prompts.base import PromptTemplate

TOPIC_XML_STRUCTURE = """<topic>
  <title>[Topic title]</title>
  <week>[Week number]</week>
  <order>[Order in week]</order>
  <content>
    <lecture>[Lecture title or description]</lecture>
    <readings>
      <reading>[Reading 1]</reading>
      <reading>[Reading 2]</reading>
    </readings>
    <objectives>
      <objective>[Learning objective 1]</objective>
      <objective>[Learning objective 2]</objective>
    </objectives>
    <notes>[Additional notes or context]</notes>
  </content>
</topic>"""

EXAMPLE_TOPIC = """<topic>
  <title>The "Hard Problem" of Consciousness</title>
  <week>1</week>
  <order>1</order>
  <content>
    <lecture>What Is It Like to Be a Bat? Defining Subjective Experience</lecture>
    <readings>
      <reading>Chalmers, David. "Facing Up to the Problem of Consciousness."</reading>
      <reading>Nagel, Thomas. "What Is It Like to Be a Bat?"</reading>
    </readings>
    <objectives>
      <objective>Define the hard problem of consciousness</objective>
      <objective>Distinguish subjective experience from functional explanation</objective>
    </objectives>
  </content>
</topic>"""

NEXT_TOPIC_PROMPT = PromptTemplate(
    template=f"""
Generate exactly one course topic in XML format.

You are filling one canonical slot in the course sequence.
The course has {{lectures_per_week}} topics per week across {{total_weeks}} weeks,
for {{total_topic_slots}} total topic slots.
Generate the topic for:
- Week {{target_week}}
- Topic {{target_order}} within that week
- Canonical slot {{target_slot_index}} of {{total_topic_slots}}

Important rules:
- Return exactly one `<topic>` element for this requested slot.
- The `<week>` value must be `{{target_week}}`.
- The `<order>` value must be `{{target_order}}`.
- Use the prior topics context to maintain progression and avoid duplication.
- This topic must introduce substantive course material for its slot.
- Escape XML-sensitive characters inside text nodes, especially `&`, `<`, and `>`.
- Do not output a recap, summary, conclusion, wrap-up, or "course review" topic unless the
  course description explicitly implies a capstone, and even then it must still teach new material.

For the topic, you can include flexible content with these simple patterns:
- Single items: <lecture>text</lecture>, <notes>text</notes>
- Lists: <readings><reading>text</reading><reading>text</reading></readings>
- Common elements: lecture, readings, objectives, concepts, notes

All content elements are optional. Keep content simple and academic.

Required XML Structure:
{TOPIC_XML_STRUCTURE}

Course Information:
{{course_xml}}

Note: If the course XML includes a <user_notes> element, those are user-provided notes for this
course — treat them as important guidance when generating content.

{{prior_topics_context}}
{{related_courses_topics_context}}

{{freeform_prompt_text}}

Example of a properly formatted topic:
{EXAMPLE_TOPIC}

Wrap your answer in <output> tags, providing only the single <topic> element.
""",
    required_vars=[
        "course_xml",
        "lectures_per_week",
        "total_weeks",
        "total_topic_slots",
        "target_week",
        "target_order",
        "target_slot_index",
        "prior_topics_context",
        "related_courses_topics_context",
        "freeform_prompt_text",
    ],
)


def get_next_topic_prompt(
    course_data: Dict[str, Any],
    *,
    target_week: int,
    target_order: int,
    prior_topics_xml: Optional[str] = None,
    related_courses_topics_context: Optional[str] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate the prompt for a single canonical course topic slot."""
    course_xml_str = partial_course_to_xml(course_data)
    lectures_per_week = int(course_data.get("lectures_per_week") or 1)
    total_weeks = int(course_data.get("total_weeks") or 1)
    total_topic_slots = lectures_per_week * total_weeks
    target_slot_index = ((target_week - 1) * lectures_per_week) + target_order

    freeform_prompt_text = (
        f"Additional context/ideas for the topics:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    prior_topics_context = ""
    if prior_topics_xml:
        prior_topics_context = (
            f"Topics already established earlier in the course:\n{prior_topics_xml}\n\n"
            "Build naturally from them. Avoid duplicates, unnecessary recaps, and premature "
            "end-of-course framing.\n"
        )
    related_courses_context = related_courses_topics_context or ""

    try:
        return NEXT_TOPIC_PROMPT.format(
            course_xml=course_xml_str,
            lectures_per_week=lectures_per_week,
            total_weeks=total_weeks,
            total_topic_slots=total_topic_slots,
            target_week=target_week,
            target_order=target_order,
            target_slot_index=target_slot_index,
            prior_topics_context=prior_topics_context,
            related_courses_topics_context=related_courses_context,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting NEXT_TOPIC_PROMPT: {e}")


TOPICS_XML_STRUCTURE = f"""<topics>
  {TOPIC_XML_STRUCTURE}
</topics>"""

TOPICS_PROMPT = PromptTemplate(
    template=f"""
Generate a complete, intellectually grounded week-by-week syllabus of course topics in XML format.

The course has {{lectures_per_week}} topics per week across {{total_weeks}} weeks,
for {{total_topic_slots}} total topic slots.

Design the Week-by-Week Curriculum:
- Organize the subject matter into a logical progression of weekly `<topic>` modules covering
  every missing slot from week 1..{{total_weeks}} and order 1..{{lectures_per_week}}.
- `<title>`: Assign a clear topic or conceptual theme to each slot that builds toward the course's
  overarching inquiry.
- `<content>`:
  - `<lecture>`: Include a sharp, evocative lecture title or conceptual focus for the session.
  - `<readings>`: Pair each topic with curated reading suggestions (foundational books, articles,
    essays, or primary works by relevant scholars, writers, and thinkers).
  - `<objectives>` (optional) and `<notes>` (optional): Key learning objectives or context.

Tone and Guardrails:
- Academic and Succinct: Write in an informative, scholarly, and concise voice that prioritizes
  conceptual structure and intellectual connections over fluff.
- Content Over Logistics: Focus strictly on the intellectual architecture (themes, lectures, and
  readings). Do not output administrative boilerplate or filler "recap / summary / course review"
  topics unless the course description explicitly implies a substantive capstone.
- Escape XML-sensitive characters inside text nodes, especially `&` (`&amp;`), `<` (`&lt;`), and `>` (`&gt;`).

Required XML Structure:
{TOPICS_XML_STRUCTURE}

Course Information:
{{course_xml}}

Note: If the course XML includes a <user_notes> element, those are user-provided notes for this
course — treat them as important guidance when generating content.

{{existing_topics_context}}
{{related_courses_topics_context}}

{{freeform_prompt_text}}

Example of a properly formatted topic inside `<topics>`:
<topics>
{EXAMPLE_TOPIC}
</topics>

Wrap your answer in <output> tags, providing only the `<topics>` element containing the `<topic>` items.
""",
    required_vars=[
        "course_xml",
        "lectures_per_week",
        "total_weeks",
        "total_topic_slots",
        "existing_topics_context",
        "related_courses_topics_context",
        "freeform_prompt_text",
    ],
)


def get_topics_prompt(
    course_data: Dict[str, Any],
    *,
    existing_topics_xml: Optional[str] = None,
    related_courses_topics_context: Optional[str] = None,
    freeform_prompt: Optional[str] = None,
) -> str:
    """Generate the prompt for the full week-by-week course topics curriculum in one call."""
    course_xml_str = partial_course_to_xml(course_data)
    lectures_per_week = int(course_data.get("lectures_per_week") or 1)
    total_weeks = int(course_data.get("total_weeks") or 1)
    total_topic_slots = lectures_per_week * total_weeks

    freeform_prompt_text = (
        f"Additional context/ideas for the topics:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    existing_topics_context = ""
    if existing_topics_xml:
        existing_topics_context = (
            f"Topics already established in the course:\n{existing_topics_xml}\n\n"
            "Generate topics for all remaining (week, order) slots so the full syllabus is "
            "complete and cohesive. Do not duplicate existing topics.\n"
        )
    related_courses_context = related_courses_topics_context or ""

    try:
        return TOPICS_PROMPT.format(
            course_xml=course_xml_str,
            lectures_per_week=lectures_per_week,
            total_weeks=total_weeks,
            total_topic_slots=total_topic_slots,
            existing_topics_context=existing_topics_context,
            related_courses_topics_context=related_courses_context,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting TOPICS_PROMPT: {e}")
