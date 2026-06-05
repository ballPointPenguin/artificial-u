"""English (en) prompt module — re-exports the default English prompts."""

from artificial_u.prompts.course import get_course_prompt
from artificial_u.prompts.department import get_department_prompt
from artificial_u.prompts.lecture import get_lecture_prompt
from artificial_u.prompts.professor import get_professor_prompt
from artificial_u.prompts.summary import get_summary_prompt
from artificial_u.prompts.system import get_system_prompt
from artificial_u.prompts.topics import get_next_topic_prompt

__all__ = [
    "get_course_prompt",
    "get_department_prompt",
    "get_lecture_prompt",
    "get_professor_prompt",
    "get_summary_prompt",
    "get_system_prompt",
    "get_next_topic_prompt",
]
