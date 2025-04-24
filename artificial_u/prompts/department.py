"""Department-related prompt templates."""

from artificial_u.prompts.base import PromptTemplate

DEPARTMENT_PROMPT = PromptTemplate(
    template="""
<examples>
  <example>
    <input>Department of Mathematics</input>
    <output>
      <department>
        <name>Mathematics</name>
        <code>MTH</code>
        <faculty>Science and Technology</faculty>
        <description>The Department of Mathematics is responsible for teaching and research in
 mathematics and its applications.</description>
      </department>
    </output>
  </example>
  <example>
    <input>Department of History</input>
    <output>
      <department>
        <name>History</name>
        <code>HIS</code>
        <faculty>Arts and Humanities</faculty>
        <description>The Department of History focuses on the study and research of past events
 and societies.</description>
      </department>
    </output>
  </example>
</examples>
Please generate an XML entry for the following department:
<input>{department_name}</input>
<output>
""",
    required_vars=["department_name"],
)


def format_existing_departments_xml(existing_departments: list[str]) -> str:
    """Format a list of department names as XML for prompt context."""
    if not existing_departments:
        return ""
    return "\n".join(
        f"  <department>{name}</department>" for name in existing_departments
    )


OPEN_DEPARTMENT_PROMPT = PromptTemplate(
    template="""
<existing_departments>
{existing_departments}
</existing_departments>
<examples>
  <example>
    <input>Department of Mathematics</input>
    <output>
      <department>
        <name>Mathematics</name>
        <code>MTH</code>
        <faculty>Science and Technology</faculty>
        <description>The Department of Mathematics is responsible for teaching and research in
 mathematics and its applications.</description>
      </department>
    </output>
  </example>
  <example>
    <input>Department of History</input>
    <output>
      <department>
        <name>History</name>
        <code>HIS</code>
        <faculty>Arts and Humanities</faculty>
        <description>The Department of History focuses on the study and research of past events
 and societies.</description>
      </department>
    </output>
  </example>
</examples>
Invent a new, typical, or creative department and generate an XML entry for it. Do not duplicate any department listed in <existing_departments>:
<output>
""",
    required_vars=["existing_departments"],
)

COURSE_DEPARTMENT_PROMPT = PromptTemplate(
    template="""
<examples>
  <example>
    <input>Course: Introduction to Astrobiology</input>
    <output>
      <department>
        <name>Astrobiology</name>
        <code>ASTB</code>
        <faculty>Science</faculty>
        <description>The Department of Astrobiology explores the origins,
        evolution, and distribution of life in the universe.</description>
      </department>
    </output>
  </example>
</examples>
Please invent a department that would offer the following course:
<input>Course: {course_name}</input>
<output>
""",
    required_vars=["course_name"],
)


def get_department_prompt(
    department_name: str = None,
    course_name: str = None,
    existing_departments: list[str] = None,
) -> str:
    """Get the appropriate department prompt based on input type."""
    existing_departments = existing_departments or []
    existing_departments_xml = format_existing_departments_xml(existing_departments)
    if department_name:
        return DEPARTMENT_PROMPT.format(department_name=department_name)
    elif course_name:
        return COURSE_DEPARTMENT_PROMPT.format(course_name=course_name)
    else:
        return OPEN_DEPARTMENT_PROMPT.format(
            existing_departments=existing_departments_xml
        )


def get_open_department_prompt(existing_departments: list[str] = None) -> str:
    """Get the open-ended department prompt (no department name supplied), with context."""
    existing_departments = existing_departments or []
    return OPEN_DEPARTMENT_PROMPT.format(
        existing_departments=format_existing_departments_xml(existing_departments)
    )
