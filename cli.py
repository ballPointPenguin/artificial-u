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
from pathlib import Path
from dotenv import load_dotenv
import traceback

from artificial_u.system import UniversitySystem
from artificial_u.config.defaults import DEPARTMENTS
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)

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

        # Initialize system
        university_system = UniversitySystem(
            anthropic_api_key=anthropic_key,
            elevenlabs_api_key=elevenlabs_key,
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

        # Show a preview of the description (it can be quite long)
        description_preview = professor.description
        if description_preview and len(description_preview) > 100:
            description_preview = description_preview[:100] + "..."
        console.print(f"Description: {description_preview}")

        # Offer to show full description
        if professor.description and len(professor.description) > 100:
            if click.confirm("Show full description?", default=False):
                console.print(Panel(professor.description, title="Full Description"))

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
        # Get the system
        system = get_system()

        # Update the system to use caching if requested
        if enable_caching and system.content_backend != "anthropic":
            console.print(
                "[yellow]Warning:[/yellow] Prompt caching is only available with the Anthropic backend"
            )

        # Enable caching if requested and using Anthropic
        if enable_caching and system.content_backend == "anthropic":
            system.enable_caching = True
            console.print(
                "[blue]Info:[/blue] Prompt caching enabled for this lecture generation"
            )

        # Check if course exists
        course = system.repository.get_course_by_code(course_code)
        if not course:
            console.print(f"[red]Error:[/red] Course {course_code} not found")
            return

        console.print(
            Panel(
                f"Generating lecture for [bold]{course_code}[/bold]",
                subtitle=f"Week {week}, Lecture {number}"
                + (f" - Topic: {topic}" if topic else ""),
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating lecture content...", total=1)

            # Generate the lecture
            lecture, course, professor = system.generate_lecture(
                course_code=course_code,
                week=week,
                number=number,
                topic=topic,
                word_count=word_count,
            )

            progress.update(task, advance=1)

        # Show success message
        console.print("[green]Lecture generated successfully![/green]")
        console.print(f"Title: {lecture.title}")
        console.print(f"Word count: approximately {len(lecture.content.split())} words")

        # Show file path
        file_path = system.get_lecture_export_path(course_code, week, number)
        if os.path.exists(file_path):
            console.print(f"\nFull lecture saved to: {file_path}")

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
            audio_path, lecture = system.create_lecture_audio(
                course_code=course_code, week=week, number=number
            )

            progress.update(task, advance=1)

        # Show success message
        console.print("[green]Audio created successfully![/green]")
        console.print(f"Saved to: {audio_path}")

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
            has_audio = "✓" if preview.get("audio_path") else "✗"

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
    """Play an audio lecture (if available)."""
    try:
        system = get_system()

        # Find the lecture to get the audio path
        course = system.repository.get_course_by_code(course_code)
        if not course:
            console.print(f"[red]Error:[/red] Course {course_code} not found")
            return

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

        audio_path = lecture.audio_path

        if not audio_path or not os.path.exists(audio_path):
            console.print(f"[red]Error:[/red] Audio file not found")
            console.print(
                "Try generating the audio first with [bold]create-audio[/bold] command"
            )
            return

        console.print(
            f"Playing lecture for [bold]{course_code}[/bold] Week {week}, Lecture {number}"
        )
        console.print(f"Audio file: {audio_path}")

        if Confirm.ask("Would you like to try playing the audio?", default=True):
            try:
                system_name = platform.system()

                if system_name == "Darwin":  # macOS
                    subprocess.run(["open", audio_path])
                elif system_name == "Windows":
                    os.startfile(audio_path)
                else:  # Linux or other
                    subprocess.run(["xdg-open", audio_path])

                console.print("[green]Audio playback initiated.[/green]")
            except Exception as e:
                console.print(f"[red]Could not play audio:[/red] {str(e)}")
                console.print(
                    f"Please open {audio_path} manually with your media player."
                )

    except Exception as e:
        console.print(f"[red]Error playing lecture:[/red] {str(e)}")


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
        if lecture.audio_path and os.path.exists(lecture.audio_path):
            console.print(f"\n[green]Audio available:[/green] {lecture.audio_path}")
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
        # Get the system
        system = get_system()

        # Update the system to use caching if requested
        if enable_caching and system.content_backend != "anthropic":
            console.print(
                "[yellow]Warning:[/yellow] Prompt caching is only available with the Anthropic backend"
            )
            enable_caching = False

        # Enable caching if requested and using Anthropic
        system.enable_caching = enable_caching and system.content_backend == "anthropic"

        # Check if course exists
        course = system.repository.get_course_by_code(course_code)
        if not course:
            console.print(f"[red]Error:[/red] Course {course_code} not found")
            return

        # Convert topics tuple to list
        topic_list = list(topics)

        console.print(
            Panel(
                f"Generating lecture series for [bold]{course_code}[/bold] with {len(topic_list)} lectures",
                title="Lecture Series Generation",
                border_style="blue",
            )
        )

        # Display course and professor info
        professor = system.repository.get_professor(course.professor_id)
        console.print(f"Course: [bold]{course.title}[/bold] ({course.code})")
        console.print(f"Professor: [bold]{professor.name}[/bold]")
        console.print(f"Starting week: [bold]{starting_week}[/bold]")
        console.print(f"Topics: [bold]{', '.join(topic_list)}[/bold]")
        console.print(
            f"Caching enabled: [bold]{'Yes' if system.enable_caching else 'No'}[/bold]"
        )

        # Start progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Generating lectures...", total=len(topic_list))

            # Define a callback for progress updates
            def update_progress():
                progress.update(task, advance=1)

            # Create lectures with progress tracking
            lectures = system.create_lecture_series(
                course_code=course_code,
                topics=topic_list,
                starting_week=starting_week,
                word_count=word_count,
            )

            # Complete the progress bar
            progress.update(task, completed=len(topic_list))

        # Display success message
        console.print(
            f"\n[green]Successfully generated {len(lectures)} lectures![/green]"
        )

        # Display lecture info
        table = Table(title=f"Lectures for {course.code}")
        table.add_column("Week")
        table.add_column("Number")
        table.add_column("Title")
        table.add_column("Word Count")

        for lecture in lectures:
            word_count = len(lecture.content.split())
            table.add_row(
                str(lecture.week_number),
                str(lecture.order_in_week),
                lecture.title,
                str(word_count),
            )

        console.print(table)

    except ContentGenerationError as e:
        console.print(f"[red]Error generating lectures:[/red] {str(e)}")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        console.print(traceback.format_exc())


if __name__ == "__main__":
    cli()
