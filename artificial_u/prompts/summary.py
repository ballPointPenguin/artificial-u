"""Lecture summary prompt template."""

from artificial_u.prompts.base import PromptTemplate

SUMMARY_XML_STRUCTURE = """
<output>
  <summary>[GENERATE]</summary>
</output>
"""

EXAMPLE_SUMMARY = """
<summary>
  The lecture introduces glacial geology with hands-on fieldwork, specimens,
  and map-based projects, emphasizing erosion, transport, and deposition.
  It covers regional focus on the Upper Midwest and Great Lakes, including
  the Laurentide Ice Sheet and the Driftless Area, and explains landforms
  such as moraines, drumlins, eskers, and kames, plus till, outwash, and
  lacustrine deposits. Announcements include distributing safety protocols,
  next week’s focus on glacier movement mechanics, ice cores, and assigned
  readings (Chapter 1 and the regional geologic map).
</summary>
"""

SUMMARY_PROMPT = PromptTemplate(
    template=f"""
Generate a new lecture summary following this XML structure:
{SUMMARY_XML_STRUCTURE}

Instructions:
- All fields (inside [GENERATE]) must be filled with generated values.
- Summarize the following lecture transcript in 50–100 words, covering the
  general topics discussed and any major announcements or activities.
- Output only the summary, wrapped in a single <summary> tag.

Example:
{EXAMPLE_SUMMARY}

Lecture Transcript:
{{lecture_content}}
""",
    required_vars=["lecture_content"],
)


def get_summary_prompt(lecture_content: str) -> str:
    """Get the summary prompt for a lecture."""
    return SUMMARY_PROMPT.format(lecture_content=lecture_content)
