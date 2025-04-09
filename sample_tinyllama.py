#!/usr/bin/env python3
"""
Sample script to demonstrate generating and viewing lectures with TinyLlama.
"""

import os
import sys
import json
from pathlib import Path

from artificial_u.system import UniversitySystem


def main():
    """Run the sample script."""
    # Check if Ollama is installed
    try:
        import ollama
    except ImportError:
        print("Ollama is not installed. Please install it with 'pip install ollama'.")
        return

    # Check if Ollama server is running
    try:
        ollama.list()
    except Exception as e:
        print(f"Ollama server is not running: {e}")
        print("Please make sure Ollama is installed and running.")
        print("Visit https://ollama.com/ for installation instructions.")
        return

    # Check if TinyLlama model is available
    models = ollama.list()
    model_names = [model.get("name", "") for model in models.get("models", [])]
    has_tinyllama = any("tinyllama" in model_name for model_name in model_names)

    if not has_tinyllama:
        print("TinyLlama model is not available. Pulling it now...")
        try:
            ollama.pull("tinyllama")
            print("Successfully pulled TinyLlama model.")
        except Exception as e:
            print(f"Failed to pull TinyLlama model: {e}")
            print("Please run 'ollama pull tinyllama' manually.")
            return

    # Initialize the system with Ollama backend
    system = UniversitySystem(
        content_backend="ollama",
        content_model="tinyllama",
        db_path="tinyllama_test.db",  # Use a specific database for this test
        text_export_path="lecture_texts",  # Export lecture text files to this directory
    )

    # Create a professor and course if they don't exist
    courses = system.list_courses()
    if not courses:
        print("Creating a sample professor and course...")
        professor = system.create_professor(
            name="Dr. Olivia Martinez",
            title="Associate Professor",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="PhD in AI from MIT, 10 years experience in NLP and machine learning",
            teaching_style="Interactive and engaging, with practical examples",
            personality="Passionate and knowledgeable with a sense of humor",
        )

        course, _ = system.create_course(
            title="Introduction to AI",
            code="CS235",
            department="Computer Science",
            professor_id=professor.id,
            description="An introductory course on artificial intelligence concepts and applications",
            weeks=10,
            lectures_per_week=2,
        )
        print(f"Created course: {course.title} ({course.code})")
    else:
        # Use the first course we find
        course = courses[0]["course"]
        print(f"Using existing course: {course.title} ({course.code})")

    # Generate a lecture if requested
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        week = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        lecture_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1

        print(f"Generating lecture for Week {week}, Lecture {lecture_num}...")
        lecture, course, professor = system.generate_lecture(
            course_code=course.code, week=week, number=lecture_num, word_count=1500
        )

        print(f"Generated lecture: {lecture.title}")
        print(
            f"Exported to: {system.get_lecture_export_path(course.code, week, lecture_num)}"
        )

    # Show a preview of lectures
    print("\nLecture Previews (Tinyllama generated):")
    previews = system.get_lecture_preview(model_filter="tinyllama")

    if not previews:
        print(
            "No tinyllama-generated lectures found. Generate some with 'python sample_tinyllama.py generate'"
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
            print(f"Audio file: {preview['audio_path'] or 'Not generated yet'}")
            print(f"Preview: {preview['content_preview']}")


if __name__ == "__main__":
    main()
