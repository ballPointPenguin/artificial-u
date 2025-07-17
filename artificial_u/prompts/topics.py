from typing import Any, Dict, Optional

from artificial_u.models.converters import partial_course_to_xml
from artificial_u.prompts.base import PromptTemplate

TOPICS_XML_STRUCTURE = """<topics>
  <course_title>[Course title]</course_title>
  <lectures_per_week>[Number of topics per week]</lectures_per_week>
  <total_weeks>[Total number of weeks in the course]</total_weeks>
  <topic>
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
  </topic>
  <!-- Add more topics as needed -->
</topics>"""

EXAMPLE_TOPICS_1 = """<topics>
  <course_title>Philosophy of Consciousness</course_title>
  <lectures_per_week>2</lectures_per_week>
  <total_weeks>12</total_weeks>
  <topic>
    <title>The "Hard Problem" of Consciousness</title>
    <week>1</week>
    <order>1</order>
    <content>
      <lecture>What is it Like to Be a Bat? Defining Subjective Experience</lecture>
      <readings>
        <reading>Chalmers, David. "Facing Up to the Problem of Consciousness."</reading>
        <reading>Nagel, Thomas. "What Is It Like to Be a Bat?"</reading>
      </readings>
    </content>
  </topic>
  <topic>
    <title>The Mind-Body Problem: Foundational Debates</title>
    <week>1</week>
    <order>2</order>
    <content>
      <lecture>Ghosts in the Machine: From Cartesian Dualism to Physicalism</lecture>
      <readings>
        <reading>Descartes, René. Meditations on First Philosophy (II & VI).</reading>
        <reading>Ryle, Gilbert. The Concept of Mind (Ch. 1).</reading>
      </readings>
    </content>
  </topic>
  <topic>
    <title>Behaviorism and the Rejection of Mind</title>
    <week>2</week>
    <order>1</order>
    <content>
      <lecture>The Black Box: Can We Understand Mind by Observing Behavior Alone?</lecture>
      <readings>
        <reading>Skinner, B.F. "The 'Operational' Analysis of Psychological Terms."</reading>
        <reading>Putnam, Hilary. "Brains and Behavior."</reading>
      </readings>
    </content>
  </topic>
  <topic>
    <title>Identity Theory and Functionalism</title>
    <week>2</week>
    <order>2</order>
    <content>
      <lecture>Is the Mind Just the Brain? States, Roles, and Realizers</lecture>
      <readings>
        <reading>Smart, J.J.C. "Sensations and Brain Processes."</reading>
        <reading>Block, Ned. "Troubles with Functionalism."</reading>
      </readings>
    </content>
  </topic>
  <!-- Additional topics omitted for brevity -->
</topics>"""

EXAMPLE_TOPICS_2 = """<topics>
  <course_title>Medieval European History</course_title>
  <lectures_per_week>3</lectures_per_week>
  <total_weeks>10</total_weeks>
  <topic>
    <title>The Fall of the Roman Empire and the Early Middle Ages</title>
    <week>1</week>
    <order>1</order>
  </topic>
  <topic>
    <title>The Rise of Feudalism and Manorialism</title>
    <week>1</week>
    <order>2</order>
  </topic>
  <topic>
    <title>The Byzantine Empire and Eastern Europe</title>
    <week>1</week>
    <order>3</order>
  </topic>
  <topic>
    <title>The Carolingian Renaissance and Charlemagne's Empire</title>
    <week>2</week>
    <order>1</order>
  </topic>
  <topic>
    <title>Viking Expansion and Its Impact on Europe</title>
    <week>2</week>
    <order>2</order>
  </topic>
  <topic>
    <title>The Development of Early Medieval Christianity</title>
    <week>2</week>
    <order>3</order>
  </topic>
  <!-- Additional topics omitted for brevity -->
</topics>"""

TOPICS_PROMPT = PromptTemplate(
    template=f"""
Generate a list of topics for a course in XML format.
Use the structure below; fill in all bracketed placeholders with either provided values
or generated ones if marked as [GENERATE].

For each topic, you can include flexible content with these simple patterns:
- Single items: <lecture>text</lecture>, <notes>text</notes>
- Lists: <readings><reading>text</reading><reading>text</reading></readings>
- Common elements: lecture, readings, objectives, concepts, notes

All content elements are optional - include what makes sense for each topic.
Keep content simple and academic.

XML Structure:
{TOPICS_XML_STRUCTURE}

Course Information:
{{course_xml}}

{{existing_topics_context}}

{{freeform_prompt_text}}

Examples of properly formatted topics:
Example 1:
{EXAMPLE_TOPICS_1}

Example 2:
{EXAMPLE_TOPICS_2}

Wrap your answer in <output> tags, providing only the <topics> element.
""",
    required_vars=["course_xml", "existing_topics_context", "freeform_prompt_text"],
)


def get_topics_prompt(
    course_data: Dict[str, Any],
    freeform_prompt: Optional[str] = None,
    existing_topics_xml: Optional[str] = None,
) -> str:
    """Generate a list of topics for a course in XML format.

    Args:
      course_data: Dictionary of course attributes.
      freeform_prompt: Optional freeform text context.
      existing_topics_xml: Optional XML of existing topics for context.

    Returns:
      Formatted prompt string.
    """
    course_xml_str = partial_course_to_xml(course_data)

    # Format freeform prompt if provided
    freeform_prompt_text = (
        f"Additional context/ideas for the topics:\n{freeform_prompt}\n" if freeform_prompt else ""
    )

    # Format existing topics context if provided
    existing_topics_context = ""
    if existing_topics_xml:
        existing_topics_context = (
            f"Existing topics for this course:\n{existing_topics_xml}\n\n"
            "Please generate topics that complement or extend the existing ones, "
            "avoiding duplicates and ensuring proper week/order sequencing.\n"
        )

    # Format the main prompt template
    try:
        return TOPICS_PROMPT.format(
            course_xml=course_xml_str,
            existing_topics_context=existing_topics_context,
            freeform_prompt_text=freeform_prompt_text,
        )
    except ValueError as e:
        raise ValueError(f"Error formatting TOPICS_PROMPT: {e}")
