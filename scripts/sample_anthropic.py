#!/usr/bin/env python3
"""
Sample script to demonstrate generating and viewing lectures with Anthropic's Claude.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from artificial_u.system import UniversitySystem


def main():
    """Run the sample script."""
    # Load environment variables
    load_dotenv()

    # Check for Anthropic API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it in your .env file or environment.")
        print("You can get an API key from: https://console.anthropic.com/")
        return

    # Initialize the system with Anthropic backend
    system = UniversitySystem(
        anthropic_api_key=api_key,
        content_backend="anthropic",  # Use Anthropic's Claude by default
        content_model="claude-3-7-sonnet-latest",  # Use Claude 3.7 Sonnet
        text_export_path="lecture_texts",  # Export lecture text files to this directory
    )

    # Create a professor and course if they don't exist
    courses = system.list_courses()
    if not courses:
        print("Creating a sample professor and course...")
        professor = system.create_professor(
            name="Dr. Elena Rossi",
            title="Professor",
            department="Computer Science",
            specialization="Natural Language Processing",
            background="PhD from Stanford, pioneering work in language models and cognitive architectures",
            teaching_style="Engaging and thought-provoking, emphasizing real-world applications",
            personality="Enthusiastic and inspiring, known for making complex concepts accessible",
            gender="Female",
            accent="Italian",
            description="Dr. Rossi has shoulder-length dark hair with subtle gray streaks that she often wears loosely styled. She has an olive complexion and expressive brown eyes that light up when discussing complex language models. Standing at 5'6\", she carries herself with confidence and grace. In the classroom, she dresses in elegant but comfortable attire, typically pairing tailored blazers with silk blouses in vibrant colors. She gestures expressively while speaking, using her hands to illustrate abstract concepts, and wears minimal jewelry except for a distinctive silver pendant shaped like a neural network that students recognize as her signature accessory.",
            age=45,
        )

        course, _ = system.create_course(
            title="Advanced Language Models",
            code="CS445",
            department="Computer Science",
            professor_id=professor.id,
            description="An advanced course exploring the architecture, capabilities, and implications of large language models",
            weeks=12,
            lectures_per_week=2,
        )
        print(f"Created course: {course.title} ({course.code})")
    else:
        # Use the first course we find
        course = courses[0]["course"]  # Extract the course object from the dictionary
        print(f"Using existing course: {course.title} ({course.code})")

    # Generate a lecture if requested
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        week = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        lecture_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1

        print(f"Generating lecture for Week {week}, Lecture {lecture_num}...")
        print("(This may take a minute as Claude crafts a detailed lecture)")

        lecture, course, professor = system.generate_lecture(
            course_code=course.code,
            week=week,
            number=lecture_num,
            word_count=2500,
        )

        print(f"Generated lecture: {lecture.title}")
        print(
            f"Exported to: {system.get_lecture_export_path(course.code, week, lecture_num)}"
        )

    # Show a preview of lectures
    print("\nLecture Previews (Claude-generated):")
    previews = system.get_lecture_preview(model_filter="claude")

    if not previews:
        print(
            "No Claude-generated lectures found. Generate some with 'python sample_anthropic.py generate'"
        )
    else:
        for preview in previews:
            print("-" * 80)
            print(f"Title: {preview['title']}")
            print(f"Course: {preview['course_title']} ({preview['course_code']})")
            print(f"Professor: {preview['professor']}")
            print(f"Week {preview['week']}, Lecture {preview['lecture_number']}")
            print(f"Generated with: {preview['model_used']}")
            print(f"Text file: {preview['text_file']}")
            print(f"Audio URL: {preview['audio_url'] or 'Not generated yet'}")
            print(f"Preview: {preview['content_preview']}")


if __name__ == "__main__":
    main()
