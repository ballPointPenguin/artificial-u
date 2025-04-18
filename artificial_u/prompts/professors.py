"""Professor prompt templates."""

from typing import Optional

from artificial_u.prompts.base import PromptTemplate

# Example professor profiles to use as demonstrations
EXAMPLE_PROFILES = [
    """Name: Dr. Eleanor Westfield, Ph.D.
Title: Associate Professor of Marine Biology
Gender: Female
Accent: American (Pacific Northwest)
Age: 42
Description: Dr. Westfield has shoulder-length auburn hair usually kept in a practical ponytail during fieldwork. She has sun-weathered skin from years of outdoor research, laugh lines around her green eyes, and typically dresses in smart casual attire paired with a signature jade pendant. Her classroom presence is energetic; she often gestures with her hands when explaining concepts and stands with confident posture developed during years of public speaking.
Background: Dr. Westfield earned her doctorate from Scripps Institution of Oceanography, focusing on coral reef ecosystems. Before joining academia, she spent five years with the National Oceanic and Atmospheric Administration studying climate change impacts on marine environments.
Personality: Known for her infectious enthusiasm and approachable demeanor, Dr. Westfield brings passion to every lecture. She uses humor effectively and is patient with students still developing their scientific thinking. Students appreciate her willingness to meet outside office hours.
Teaching Style: Dr. Westfield emphasizes hands-on learning, frequently incorporating field trips to coastal areas. Her lectures feature stunning visuals from her research expeditions, and she regularly brings artifacts from her collection for students to examine. She uses storytelling to explain complex ecological relationships.""",
    """Name: Dr. Hiro Tanaka, Ph.D.
Title: Professor of Theoretical Physics
Gender: Male
Accent: Japanese (mild)
Age: 61
Description: Dr. Tanaka has salt-and-pepper hair cropped short and meticulously groomed, with a clean-shaven face and rectangular glasses that frame his observant dark eyes. He stands 5'8" with excellent posture and typically wears formal attire—pressed dress shirts, slacks, and occasionally a tweed jacket with leather elbow patches. He moves with deliberate precision, often using his hands to illustrate concepts in space when explaining complex theories. A small analog watch is always visible on his left wrist, which he occasionally glances at while lecturing.
Background: With degrees from Tokyo University and MIT, Dr. Tanaka worked at CERN before joining the university. His contributions to string theory have been published in Nature and Science, and he maintains research collaborations with physicists worldwide.
Personality: Methodical and precise, Dr. Tanaka has a quiet intensity that commands attention. Though initially perceived as reserved, students discover his dry wit and deep commitment to their success. He values precision in language and expects rigorous thinking.
Teaching Style: Dr. Tanaka's lectures are masterclasses in logical progression. He builds complex theories step by step, using elegant derivations rather than memorization. He's known for thought experiments that make abstract concepts tangible and creates custom simulations to visualize quantum phenomena.""",
]

# Professor generation prompt template
PROFESSOR_GENERATION_PROMPT = PromptTemplate(
    template="""Create a detailed profile for a professor in the {department} department, specializing in {specialization}.

{gender_text}
{nationality_text}
{age_text}
{accent_text}

Create a rich, realistic faculty profile with the following structure:

<professor_profile>
Name: [Full name with title]
Title: [Academic title]
Gender: [Professor's gender]
Accent: [Professor's accent or speech pattern]
Age: [Professor's age as a number]
Description: [Detailed physical appearance, clothing style, mannerisms, and distinctive visual characteristics]
Background: [Educational and professional background]
Personality: [Personality traits evident in teaching]
Teaching Style: [Distinctive teaching approach]
</professor_profile>

The "Description" should provide a detailed physical appearance including facial features, body language, clothing style, and any distinctive visual characteristics that would help visualize the professor.

Here are two examples of well-crafted professor profiles:

Example 1:
<professor_profile>
{example_1}
</professor_profile>

Example 2:
<professor_profile>
{example_2}
</professor_profile>

Make this professor feel like a real person with depth. Include educational background, personality traits that show in teaching, and a distinctive teaching style.""",
    required_vars=["department", "specialization"],
)


def get_professor_prompt(
    department: str,
    specialization: str,
    gender: Optional[str] = None,
    nationality: Optional[str] = None,
    age_range: Optional[str] = None,
    accent: Optional[str] = None,
) -> str:
    """Generate a professor creation prompt.

    Args:
        department: Academic department
        specialization: Area of expertise
        gender: Optional gender specification
        nationality: Optional nationality specification
        age_range: Optional age range (e.g., "30-40", "50-60")
        accent: Optional accent specification

    Returns:
        str: Formatted prompt string
    """
    # Optional context lines
    gender_text = f"Gender: {gender}" if gender else ""
    nationality_text = (
        f"Nationality/cultural background: {nationality}" if nationality else ""
    )
    age_text = f"Age range: {age_range}" if age_range else ""
    accent_text = f"Accent: {accent}" if accent else ""

    # Format the prompt
    return PROFESSOR_GENERATION_PROMPT(
        department=department,
        specialization=specialization,
        gender_text=gender_text,
        nationality_text=nationality_text,
        age_text=age_text,
        accent_text=accent_text,
        example_1=EXAMPLE_PROFILES[0],
        example_2=EXAMPLE_PROFILES[1],
    )
