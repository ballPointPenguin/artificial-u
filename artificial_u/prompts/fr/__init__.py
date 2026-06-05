"""Module d'invites en français (fr) pour ArtificialU."""

from artificial_u.prompts.fr.course import get_course_prompt
from artificial_u.prompts.fr.department import get_department_prompt
from artificial_u.prompts.fr.lecture import get_lecture_prompt
from artificial_u.prompts.fr.professor import get_professor_prompt
from artificial_u.prompts.fr.summary import get_summary_prompt
from artificial_u.prompts.fr.system import get_system_prompt
from artificial_u.prompts.fr.topics import get_next_topic_prompt

__all__ = [
    "get_course_prompt",
    "get_department_prompt",
    "get_lecture_prompt",
    "get_professor_prompt",
    "get_summary_prompt",
    "get_system_prompt",
    "get_next_topic_prompt",
]
