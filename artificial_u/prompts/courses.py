"""Course-related prompt templates."""

from artificial_u.config.defaults import DEFAULT_COURSE_WEEKS, DEFAULT_LECTURES_PER_WEEK
from artificial_u.prompts.base import PromptTemplate

# XML structure for course topics
COURSE_XML_STRUCTURE = """<course>
  <code>[Course code]</code>
  <title>[Course title]</title>
  <description>[Course description]</description>
  <level>[Course level]</level>
  <credits>[Course credits]</credits>
  <lectures_per_week>[Course lectures per week]</lectures_per_week>
  <total_weeks>[Course total weeks]</total_weeks>
  <topics>
    <week number="[Week number]">
      <lecture number="1">
        <topic>[Topic for first lecture of the week]</topic>
      </lecture>
      <lecture number="2">
        <topic>[Topic for second lecture of the week, if lectures_per_week > 1]</topic>
      </lecture>
      <!-- Add more lectures as needed based on lectures_per_week -->
    </week>
    <!-- Repeat for each week up to total_weeks -->
  </topics>
</course>"""

# Example courses to demonstrate the format
EXAMPLE_COURSE_1 = """<course>
  <code>CS101</code>
  <title>Introduction to Computer Science</title>
  <description>A beginner-friendly introduction to computer science principles, programming basics,
  and computational thinking.</description>
  <level>Undergraduate</level>
  <credits>3</credits>
  <lectures_per_week>2</lectures_per_week>
  <total_weeks>12</total_weeks>
  <topics>
    <week number="1">
      <lecture number="1">
        <topic>Introduction to Computer Science and Computational Thinking</topic>
      </lecture>
      <lecture number="2">
        <topic>History of Computing and Binary Number Systems</topic>
      </lecture>
    </week>
    <week number="2">
      <lecture number="1">
        <topic>Introduction to Programming: Basic Syntax and Variables</topic>
      </lecture>
      <lecture number="2">
        <topic>Control Structures: Conditionals and Loops</topic>
      </lecture>
    </week>
    <!-- Additional weeks omitted for brevity -->
  </topics>
</course>"""

EXAMPLE_COURSE_2 = """<course>
  <code>HIST220</code>
  <title>Medieval European History</title>
  <description>An exploration of European history from the fall of Rome to the Renaissance, examining
  social, political, and cultural developments.</description>
  <level>Undergraduate</level>
  <credits>4</credits>
  <lectures_per_week>3</lectures_per_week>
  <total_weeks>10</total_weeks>
  <topics>
    <week number="1">
      <lecture number="1">
        <topic>The Fall of the Roman Empire and the Early Middle Ages</topic>
      </lecture>
      <lecture number="2">
        <topic>The Rise of Feudalism and Manorialism</topic>
      </lecture>
      <lecture number="3">
        <topic>The Byzantine Empire and Eastern Europe</topic>
      </lecture>
    </week>
    <week number="2">
      <lecture number="1">
        <topic>The Carolingian Renaissance and Charlemagne's Empire</topic>
      </lecture>
      <lecture number="2">
        <topic>Viking Expansion and Its Impact on Europe</topic>
      </lecture>
      <lecture number="3">
        <topic>The Development of Early Medieval Christianity</topic>
      </lecture>
    </week>
    <!-- Additional weeks omitted for brevity -->
  </topics>
</course>"""

# Unified course prompt that handles both structured and freeform inputs
COURSE_PROMPT = PromptTemplate(
    template=f"""
Generate a course with a nested sequence of lecture topics in XML format.
Use the structure below; fill in all bracketed placeholders with either provided values or generated ones if marked as [GENERATE].

XML Structure:
{COURSE_XML_STRUCTURE}

Existing courses in this department (for context and to avoid repetition):
{{existing_courses_xml}}

Department Information:
{{department_xml}}

Professor Information:
{{professor_xml}}

Partial Course Details:
{{partial_course_xml}}

{{freeform_prompt_text}}

Examples of properly formatted courses:
Example 1:
{EXAMPLE_COURSE_1}

Example 2:
{EXAMPLE_COURSE_2}

IMPORTANT: Make sure that the number of lectures per week in your response matches the specified lectures_per_week value.
For each week, generate exactly the number of lectures specified in lectures_per_week.

Wrap your answer in <output> tags, providing only the <course> element:
<output>
""",
    required_vars=[
        "existing_courses_xml",
        "partial_course_xml",
        "professor_xml",
        "department_xml",
    ],
)


def format_existing_courses_xml(existing_courses):
    """Format a list of existing courses as XML for context."""
    if not existing_courses:
        return "<no_existing_courses />"

    lines = ["<existing_courses>"]
    for course in existing_courses:
        lines.append("  <course>")
        lines.append(f"    <code>{course.get('code', 'N/A')}</code>")
        lines.append(f"    <title>{course.get('title', 'N/A')}</title>")
        lines.append(
            f"    <description>{course.get('description', 'N/A')}</description>"
        )

        # Add topic overview if available
        if course.get("topics"):
            lines.append("    <topics_overview>")
            for topic in course.get("topics", [])[
                :5
            ]:  # Limit to first 5 topics for brevity
                lines.append(f"      <topic>{topic}</topic>")
            if len(course.get("topics", [])) > 5:
                lines.append(
                    f"      <additional_topics_count>{len(course.get('topics', [])) - 5}</additional_topics_count>"
                )
            lines.append("    </topics_overview>")

        lines.append("  </course>")
    lines.append("</existing_courses>")
    return "\n".join(lines)


def format_partial_course_xml(partial_attrs: dict) -> str:
    """Builds the XML string for partial course attributes, marking missing fields as [GENERATE]."""
    lines = ["<course>"]
    # Define all expected fields in the desired order
    fields = [
        "code",
        "title",
        "description",
        "level",
        "credits",
        "lectures_per_week",
        "total_weeks",
    ]

    for field in fields:
        value = partial_attrs.get(field)
        # Handle provided attributes
        if value is not None and value != "[GENERATE]":
            lines.append(f"  <{field}>{str(value)}</{field}>")
        else:
            lines.append(f"  <{field}>[GENERATE]</{field}>")

    # If topics are provided, add them
    if "topics" in partial_attrs and partial_attrs["topics"]:
        lines.append("  <topics>")
        for topic in partial_attrs["topics"]:
            week = topic.get("week", "[GENERATE]")
            lecture = topic.get("lecture", 1)
            topic_text = topic.get("topic", "[GENERATE]")
            lines.append(f'    <week number="{week}">')
            lines.append(f'      <lecture number="{lecture}">')
            lines.append(f"        <topic>{topic_text}</topic>")
            lines.append("      </lecture>")
            lines.append("    </week>")
        lines.append("  </topics>")
    else:
        lines.append("  <topics>[GENERATE]</topics>")

    lines.append("</course>")
    return "\n".join(lines)


def get_course_prompt(
    course_title: str = "[GENERATE]",
    course_code: str = "[GENERATE]",
    course_description: str = "[GENERATE]",
    course_level: str = "[GENERATE]",
    course_credits: str = "[GENERATE]",
    lectures_per_week: int = DEFAULT_LECTURES_PER_WEEK,
    total_weeks: int = DEFAULT_COURSE_WEEKS,
    department_xml: str = None,
    professor_xml: str = None,
    existing_courses: list = None,
    topics: list = None,
    freeform_prompt: str = None,
) -> str:
    """Generate a course topics prompt with optional prepopulated fields.

    Args:
        course_title: Course title or [GENERATE] to have the model generate it
        course_code: Course code or [GENERATE] to have the model generate it
        course_description: Course description or [GENERATE] to have the model generate it
        course_level: Course level or [GENERATE] to have the model generate it
        course_credits: Course credits or [GENERATE] to have the model generate it
        lectures_per_week: Number of lectures per week
        total_weeks: Total number of weeks in the course
        department_xml: Required XML representation of the department
        professor_xml: Required XML representation of the professor
        existing_courses: Optional list of existing courses for context
        topics: Optional list of predefined topics as {"week": w, "lecture": l, "topic": t}
        freeform_prompt: Optional freeform text to provide additional context

    Returns:
        Formatted prompt string
    """
    if department_xml is None or professor_xml is None:
        raise ValueError("Both department_xml and professor_xml are required")

    # Format existing courses as XML if provided
    existing_courses_xml = format_existing_courses_xml(existing_courses or [])

    # Build partial course XML from provided attributes
    partial_attrs = {
        "code": course_code,
        "title": course_title,
        "description": course_description,
        "level": course_level,
        "credits": course_credits,
        "lectures_per_week": lectures_per_week,
        "total_weeks": total_weeks,
        "topics": topics,
    }

    partial_course_xml = format_partial_course_xml(partial_attrs)

    # Format freeform prompt if provided
    freeform_prompt_text = ""
    if freeform_prompt:
        freeform_prompt_text = "Additional context/ideas for the course:\n{}\n".format(
            freeform_prompt
        )

    return COURSE_PROMPT.format(
        existing_courses_xml=existing_courses_xml,
        partial_course_xml=partial_course_xml,
        professor_xml=professor_xml,
        department_xml=department_xml,
        freeform_prompt_text=freeform_prompt_text,
    )
