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

OPEN_DEPARTMENT_PROMPT = PromptTemplate(
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
Invent a new, typical, or creative department and generate an XML entry for it:
<output>
""",
    required_vars=[],
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


def get_department_prompt(department_name: str) -> str:
    """Get the department prompt for a given department name."""
    return DEPARTMENT_PROMPT.format(department_name=department_name)


def get_open_department_prompt() -> str:
    """Get the open-ended department prompt (no department name supplied)."""
    return OPEN_DEPARTMENT_PROMPT.format()


def get_course_department_prompt(course_name: str) -> str:
    """Get the department prompt for a given course name."""
    return COURSE_DEPARTMENT_PROMPT.format(course_name=course_name)
