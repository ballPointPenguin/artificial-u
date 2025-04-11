#!/usr/bin/env python3
"""
Command-Line Interface for ArtificialU.

A simplified CLI providing access to core system functionality.
"""

import os
import sys
import click
import platform
import subprocess
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import traceback
from typing import Optional, List, Dict

from artificial_u.system import UniversitySystem
from artificial_u.config.defaults import DEPARTMENTS
from artificial_u.utils.exceptions import ContentGenerationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)
from rich.syntax import Syntax

# Load environment variables
load_dotenv()

console = Console()
university_system = None


def get_system():
    """Get or create the university system instance."""
    global university_system

    if university_system is None:
        # Get API keys from environment
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")

        # Initialize system (Removed audio_path, text_export_path)
        university_system = UniversitySystem(
            anthropic_api_key=anthropic_key,
            elevenlabs_api_key=elevenlabs_key,
            db_url=os.environ.get("DATABASE_URL"),
            content_backend=os.environ.get("CONTENT_BACKEND"),
            content_model=os.environ.get("CONTENT_MODEL"),
            log_level=os.environ.get("LOG_LEVEL"),
        )

    return university_system


@click.group()
def cli():
    """ArtificialU - AI-generated university lectures with professor personalities."""
    pass


@cli.command()
@click.option("--department", "-d", required=True, help="Department name")
@click.option("--title", "-t", required=True, help="Course title")
@click.option("--code", "-c", required=True, help="Course code")
@click.option(
    "--professor-id", "-p", help="Specify professor ID (creates new if not specified)"
)
@click.option("--weeks", default=14, type=int, help="Number of weeks")
@click.option("--lectures-per-week", default=2, type=int, help="Lectures per week")
@click.option(
    "--description", help="Course description (auto-generated if not provided)"
)
def create_course(
    department, title, code, professor_id, weeks, lectures_per_week, description
):
    """Create a new course with syllabus."""
    try:
        system = get_system()

        # Validate department
        if department not in DEPARTMENTS:
            if not Confirm.ask(
                f"[yellow]Warning:[/yellow] '{department}' is not a standard department. Continue?",
                default=True,
            ):
                return

        console.print(
            Panel(
                f"Creating course: [bold]{title}[/bold]",
                subtitle=f"Department: {department}, Code: {code}",
            )
        )

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Creating course and generating syllabus...", total=None
            )

            # Create the course
            course, professor = system.create_course(
                title=title,
                code=code,
                department=department,
                professor_id=professor_id,
                description=description,
                weeks=weeks,
                lectures_per_week=lectures_per_week,
            )

            progress.update(task, visible=False)

        # Show success message
        console.print("[green]Course created successfully![/green]")
        console.print(f"Course ID: {course.id}")
        console.print(f"Professor: {professor.name} (ID: {professor.id})")

    except Exception as e:
        console.print(f"[red]Error creating course:[/red] {str(e)}")


@cli.command()
@click.option("--department", "-d", help="Filter by department")
def list_courses(department):
    """List all available courses."""
    try:
        system = get_system()
        courses_info = system.list_courses(department)

        if not courses_info:
            console.print("[yellow]No courses found.[/yellow]")
            return

        # Display in a table
        table = Table("Code", "Title", "Department", "Professor")

        for info in courses_info:
            course = info["course"]
            professor = info["professor"]

            table.add_row(
                course.code,
                course.title,
                course.department,
                professor.name,
            )

        console.print(Panel("Available Courses", subtitle="Artificial University"))
        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing courses:[/red] {str(e)}")


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
def show_syllabus(course_code):
    """Display a course syllabus."""
    try:
        system = get_system()
        course = system.repository.get_course_by_code(course_code)
        if not course:
            console.print(f"[red]Course {course_code} not found[/red]")
            return

        professor = system.repository.get_professor(course.professor_id)

        # Display syllabus
        if course.syllabus:
            title = (
                f"# {course.title} ({course.code})\n\n## Professor: {professor.name}"
            )

            if not course.syllabus.startswith("#"):
                formatted_syllabus = f"{title}\n\n{course.syllabus}"
            else:
                formatted_syllabus = course.syllabus

            console.print(Markdown(formatted_syllabus))
        else:
            console.print("[yellow]No syllabus available for this course.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@cli.command()
def list_professors():
    """List all professors."""
    try:
        system = get_system()
        professors = system.repository.list_professors()

        if not professors:
            console.print("[yellow]No professors found.[/yellow]")
            return

        # Display in a table
        table = Table("ID", "Name", "Department", "Specialization")

        for professor in professors:
            table.add_row(
                professor.id,
                professor.name,
                professor.department,
                professor.specialization,
            )

        console.print(Panel("Faculty Directory", subtitle="Artificial University"))
        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing professors:[/red] {str(e)}")


@cli.command()
@click.option("--name", help="Professor name (AI-generated if not provided)")
@click.option("--department", "-d", help="Department (AI-generated if not provided)")
@click.option(
    "--specialization", "-s", help="Specialization (AI-generated if not provided)"
)
@click.option("--gender", "-g", help="Gender (AI-generated if not provided)")
@click.option("--accent", "-a", help="Accent (AI-generated if not provided)")
@click.option("--age", type=int, help="Age (AI-generated if not provided)")
@click.option("--title", "-t", help="Academic title (AI-generated if not provided)")
@click.option("--background", "-b", help="Background (AI-generated if not provided)")
def create_professor(
    name, department, specialization, gender, accent, age, title, background
):
    """Create a new professor with AI-generated attributes."""
    try:
        system = get_system()

        console.print(
            Panel(
                f"Creating professor with AI{f': [bold]{name}[/bold]' if name else ''}",
                subtitle=f"{department or 'AI-generated department'} - {specialization or 'AI-generated specialization'}",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating professor with AI...", total=None)

            # Create the professor with all available parameters
            professor = system.create_professor(
                name=name,
                department=department,
                specialization=specialization,
                gender=gender,
                accent=accent,
                age=age,
                title=title,
                background=background,
            )

            progress.update(task, visible=False)

        # Show success message with details
        console.print("[green]Professor created successfully with AI![/green]")
        console.print(f"ID: {professor.id}")
        console.print(f"Name: {professor.name}")
        console.print(f"Gender: {professor.gender}")
        console.print(f"Accent: {professor.accent}")
        console.print(f"Age: {professor.age}")
        console.print(f"Title: {professor.title}")
        console.print(f"Department: {professor.department}")
        console.print(f"Specialization: {professor.specialization}")
        console.print(f"Background: {professor.background}")
        console.print(f"Personality: {professor.personality}")
        console.print(f"Teaching Style: {professor.teaching_style}")
        console.print(f"Description: {professor.description}")

    except Exception as e:
        console.print(f"[red]Error creating professor:[/red] {str(e)}")


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
@click.option("--week", "-w", required=True, type=int, help="Week number")
@click.option(
    "--number", "-n", default=1, type=int, help="Lecture number within the week"
)
@click.option(
    "--topic", "-t", help="Lecture topic (uses syllabus topic if not specified)"
)
@click.option("--word-count", default=2500, type=int, help="Target word count")
@click.option(
    "--enable-caching/--no-caching",
    default=False,
    help="Enable prompt caching to reduce token usage and maintain consistent style (Anthropic only)",
)
def generate_lecture(course_code, week, number, topic, word_count, enable_caching):
    """Generate a lecture for a course."""
    try:
        system = get_system()

        console.print(
            Panel(
                f"Generating lecture for [bold]{course_code}[/bold]",
                subtitle=f"Week {week}, Lecture {number}",
            )
        )

        # Modify system's caching setting if needed
        if enable_caching:
            system.config.enable_caching = True

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task1 = progress.add_task("Generating lecture content...", total=1)

            # Generate the lecture
            lecture, course, professor = system.generate_lecture(
                course_code=course_code,
                week=week,
                number=number,
                topic=topic,
                word_count=word_count,
            )

            progress.update(task1, advance=1)
            task2 = progress.add_task("Exporting lecture text...", total=1)

            # Export the lecture text
            loop = asyncio.get_event_loop()
            export_path = loop.run_until_complete(
                system.export_lecture_text(lecture, course, professor)
            )

            progress.update(task2, advance=1)

        # Show success message
        console.print("[green]Lecture generated successfully![/green]")
        console.print(f"Title: {lecture.title}")
        console.print(f"Word count: ~{len(lecture.content.split())} words")
        console.print(f"Text exported to: {export_path}")

        # Ask if user wants to view the lecture
        if Confirm.ask("View lecture now?"):
            console.print("\n")
            console.print(
                Panel(
                    f"[bold]{lecture.title}[/bold]",
                    subtitle=f"{course_code} - {professor.name}",
                )
            )
            console.print(Markdown(lecture.content))

        # Ask if user wants to generate audio
        if Confirm.ask("Generate audio for this lecture?"):
            loop = asyncio.get_event_loop()
            audio_url, _ = loop.run_until_complete(
                system.create_lecture_audio(
                    course_code=course_code, week=week, number=number
                )
            )
            console.print(f"[green]Audio created at URL:[/green] {audio_url}")

    except Exception as e:
        console.print(f"[red]Error generating lecture:[/red] {str(e)}")


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
@click.option("--week", "-w", required=True, type=int, help="Week number")
@click.option(
    "--number", "-n", default=1, type=int, help="Lecture number within the week"
)
def create_audio(course_code, week, number):
    """Convert a lecture to audio using ElevenLabs API."""
    try:
        system = get_system()

        console.print(
            Panel(
                f"Creating audio for [bold]{course_code}[/bold]",
                subtitle=f"Week {week}, Lecture {number}",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating audio...", total=1)

            # Create the audio
            loop = asyncio.get_event_loop()
            audio_url, lecture = loop.run_until_complete(
                system.create_lecture_audio(
                    course_code=course_code, week=week, number=number
                )
            )

            progress.update(task, advance=1)

        # Show success message
        console.print("[green]Audio created successfully![/green]")
        console.print(f"Saved to URL: {audio_url}")

    except Exception as e:
        console.print(f"[red]Error creating audio:[/red] {str(e)}")


@cli.command()
@click.option("--course-code", "-c", help="Filter by course code")
@click.option("--limit", "-l", default=5, help="Maximum number of lectures to show")
@click.option("--model", "-m", help="Filter by model (e.g., 'tinyllama')")
def list_lectures(course_code, limit, model):
    """List available lectures."""
    try:
        system = get_system()
        previews = system.get_lecture_preview(
            course_code=course_code, model_filter=model, limit=limit
        )

        if not previews:
            console.print("[yellow]No lectures found.[/yellow]")
            return

        # Display in a table
        table = Table("Course", "Week", "#", "Title", "Audio")

        for preview in previews:
            has_audio = "✓" if preview.get("audio_url") else "✗"

            table.add_row(
                preview.get("course_code", ""),
                str(preview.get("week", "")),
                str(preview.get("lecture_number", "")),
                preview.get("title", ""),
                has_audio,
            )

        console.print(
            Panel(
                "Recent Lectures",
                subtitle=f"{course_code or 'All courses'}"
                + (f" - {model} model" if model else ""),
            )
        )
        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing lectures:[/red] {str(e)}")


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
@click.option("--week", "-w", required=True, type=int, help="Week number")
@click.option(
    "--number", "-n", default=1, type=int, help="Lecture number within the week"
)
def play_lecture(course_code, week, number):
    """Play audio for an existing lecture."""
    try:
        system = get_system()

        # Check if lecture exists
        lectures = system.get_lecture_preview(course_code=course_code)
        lecture = next(
            (
                l
                for l in lectures
                if l["course_code"] == course_code
                and l["week"] == week
                and l["number"] == number
            ),
            None,
        )

        if not lecture:
            console.print(
                f"[red]Lecture for {course_code}, week {week}, number {number} not found.[/red]"
            )
            return

        if not lecture.get("audio_url"):
            console.print("[yellow]No audio available for this lecture.[/yellow]")

            # Ask if user wants to generate audio
            if Confirm.ask("Generate audio now?"):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task("Generating audio...", total=1)

                    # Create the audio using asyncio
                    loop = asyncio.get_event_loop()
                    audio_url, _ = loop.run_until_complete(
                        system.create_lecture_audio(
                            course_code=course_code, week=week, number=number
                        )
                    )

                    progress.update(task, advance=1)

                console.print(f"[green]Audio created at URL:[/green] {audio_url}")

                # Update the lecture info with the new audio url
                lecture["audio_url"] = audio_url
            else:
                return

        audio_url = lecture["audio_url"]
        console.print(
            Panel(
                f"Playing audio for [bold]{lecture['title']}[/bold]",
                subtitle=f"{course_code}, Week {week}, Lecture {number}",
            )
        )

        # Play the audio using asyncio
        try:
            console.print("[green]Playing...[/green]")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(system.play_audio(audio_url))
        except Exception as e:
            console.print(f"[red]Error playing audio:[/red] {str(e)}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        import traceback

        traceback.print_exc()


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
@click.option("--week", "-w", required=True, type=int, help="Week number")
@click.option(
    "--number", "-n", default=1, type=int, help="Lecture number within the week"
)
def show_lecture(course_code, week, number):
    """Display a generated lecture content."""
    try:
        system = get_system()
        course = system.repository.get_course_by_code(course_code)
        if not course:
            console.print(f"[red]Error:[/red] Course {course_code} not found")
            return

        # Get the lecture
        lecture = system.repository.get_lecture_by_course_week_order(
            course_id=course.id, week_number=week, order_in_week=number
        )

        if not lecture:
            console.print(
                f"[red]Error:[/red] Lecture not found for {course_code}, Week {week}, Number {number}"
            )
            console.print(
                "Try generating the lecture first with [bold]generate-lecture[/bold] command"
            )
            return

        # Display lecture content as markdown
        console.print(Markdown(lecture.content))

        # Show audio status
        if lecture.audio_url:
            console.print(
                f"\n[green]Audio available at URL:[/green] {lecture.audio_url}"
            )
        else:
            console.print(f"\n[yellow]No audio available.[/yellow]")
            console.print("Generate audio with [bold]create-audio[/bold] command")

    except Exception as e:
        console.print(f"[red]Error displaying lecture:[/red] {str(e)}")


@cli.command()
@click.argument("course-code")
@click.argument("topics", nargs=-1, required=True)
@click.option("--starting-week", "-w", default=1, type=int, help="Starting week number")
@click.option(
    "--word-count", default=2500, type=int, help="Target word count per lecture"
)
@click.option(
    "--enable-caching/--no-caching",
    default=True,
    help="Enable prompt caching for consistency and reduced token usage (Anthropic only)",
)
def generate_lecture_series(
    course_code, topics, starting_week, word_count, enable_caching
):
    """Generate a series of related lectures for a course.

    This command creates multiple lectures in sequence, maintaining the professor's
    voice and teaching style across all lectures. It's more efficient than creating
    lectures one-by-one as it leverages prompt caching for reduced token usage.

    Example:
        ./cli.py generate-lecture-series CS101 "Introduction to Programming" "Variables and Data Types" "Control Flow"
    """
    try:
        system = get_system()

        # Check if course exists
        courses = system.list_courses()
        course = next((c for c in courses if c["code"] == course_code), None)
        if not course:
            console.print(f"[red]Course with code {course_code} not found.[/red]")
            return

        console.print(
            Panel(
                f"Generating lecture series for [bold]{course['title']}[/bold] ({course_code})",
                subtitle=f"Starting from week {starting_week}, {len(topics)} lectures",
            )
        )

        # Modify system's caching setting if needed
        if enable_caching:
            system.config.enable_caching = True

        # Define function to update progress
        def update_progress():
            """Track progress for the lecture series generation."""
            nonlocal task, progress
            progress.update(task, advance=1)

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating lecture series...", total=len(topics))

            # Generate the lecture series
            lecture_series = system.create_lecture_series(
                course_code=course_code,
                topics=topics,
                starting_week=starting_week,
                word_count=word_count,
                progress_callback=update_progress,
            )

        # Show success message
        console.print("[green]Lecture series generated successfully![/green]")

        # Create table
        table = Table(title=f"Generated Lectures for {course_code}")
        table.add_column("Week", style="green")
        table.add_column("Number", style="green")
        table.add_column("Title", style="blue")
        table.add_column("Word Count", style="yellow")

        # Add lectures to table
        for lecture in lecture_series:
            table.add_row(
                str(lecture.week_number),
                str(lecture.order_in_week),
                lecture.title,
                str(len(lecture.content.split())),
            )

        console.print(table)

    except ContentGenerationError as e:
        console.print(f"[red]Error generating lectures:[/red] {str(e)}")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        console.print(traceback.format_exc())


if __name__ == "__main__":
    cli()
