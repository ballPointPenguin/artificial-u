"""Course-related prompt templates."""

from artificial_u.config.defaults import DEFAULT_COURSE_WEEKS, DEFAULT_LECTURES_PER_WEEK
from artificial_u.prompts.base import PromptTemplate

# Course syllabus template
SYLLABUS_PROMPT = PromptTemplate(
    template="""Create a detailed course syllabus for {course_code}: {course_title}

Course Information:
- Department: {department}
- Professor: {professor_name} ({professor_title})
- Teaching Style: {teaching_style}

Create a comprehensive syllabus with the following structure:

<syllabus>
Course Description: [Overview of the course and its objectives]

Learning Outcomes:
[List of 4-6 specific outcomes students will achieve]

Course Structure:
[Weekly breakdown of topics and activities]

Assessment Methods:
[Description of how students will be evaluated]

Required Materials:
[List of necessary textbooks, resources, or materials]

Course Policies:
[Key policies on attendance, participation, and academic integrity]
</syllabus>

Make this syllabus clear, professional, and aligned with the professor's teaching style.""",
    required_vars=[
        "course_code",
        "course_title",
        "department",
        "professor_name",
        "professor_title",
        "teaching_style",
    ],
)

# Course topic generator template
COURSE_TOPICS_PROMPT = PromptTemplate(
    template="""Generate a coherent sequence of {num_weeks} weeks of lecture topics for the course
 "{course_title}" ({course_code}) in the {department} department.

The course is taught by {professor_name}, whose teaching style is: {teaching_style}

The course description is:
{course_description}

Create a week-by-week breakdown of course topics that build logically on each other and cover the
 subject matter comprehensively.

<course_topics>
{topic_format}
</course_topics>

Ensure the topics follow a logical progression, building in complexity throughout the course, and
 align with the course description.""",
    required_vars=[
        "course_title",
        "course_code",
        "department",
        "professor_name",
        "teaching_style",
        "course_description",
        "num_weeks",
        "topic_format",
    ],
)

# Default topic format for the course topics prompt
DEFAULT_TOPIC_FORMAT = """Week 1:
- Lecture 1: [Topic]
- Lecture 2: [Topic]

Week 2:
- Lecture 1: [Topic]
- Lecture 2: [Topic]

[... continue for all weeks ...]"""


def get_syllabus_prompt(
    course_code: str,
    course_title: str,
    department: str,
    professor_name: str,
    professor_title: str,
    teaching_style: str,
) -> str:
    """Generate a course syllabus prompt.

    Args:
        course_code: Course code (e.g., CS101)
        course_title: Course title
        department: Academic department
        professor_name: Name of the professor
        professor_title: Title of the professor
        teaching_style: Professor's teaching style

    Returns:
        str: Formatted syllabus prompt
    """
    return SYLLABUS_PROMPT(
        course_code=course_code,
        course_title=course_title,
        department=department,
        professor_name=professor_name,
        professor_title=professor_title,
        teaching_style=teaching_style,
    )


def get_course_topics_prompt(
    course_title: str,
    course_code: str,
    department: str,
    professor_name: str,
    teaching_style: str,
    course_description: str,
    num_weeks: int = DEFAULT_COURSE_WEEKS,
    topics_per_week: int = DEFAULT_LECTURES_PER_WEEK,
) -> str:
    """Generate a course topics prompt.

    Args:
        course_title: Course title
        course_code: Course code
        department: Academic department
        professor_name: Name of the professor
        teaching_style: Professor's teaching style
        course_description: Description of the course
        num_weeks: Number of weeks in the course
        topics_per_week: Number of topics per week

    Returns:
        str: Formatted course topics prompt
    """
    # Create topic format based on number of weeks and topics per week
    topic_format = ""
    for week in range(1, num_weeks + 1):
        topic_format += f"Week {week}:\n"
        for lecture in range(1, topics_per_week + 1):
            topic_format += f"- Lecture {lecture}: [Topic]\n"
        topic_format += "\n"

    return COURSE_TOPICS_PROMPT(
        course_title=course_title,
        course_code=course_code,
        department=department,
        professor_name=professor_name,
        teaching_style=teaching_style,
        course_description=course_description,
        num_weeks=num_weeks,
        topic_format=topic_format,
    )
