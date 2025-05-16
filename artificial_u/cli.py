#!/usr/bin/env python3
"""
Command-Line Interface for ArtificialU.

A simplified CLI providing access to core system functionality.
"""

import asyncio
import os
import traceback

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm
from rich.table import Table

from artificial_u.config.defaults import DEPARTMENTS
from artificial_u.system import UniversitySystem

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
        google_key = os.environ.get("GOOGLE_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        speech_key = os.environ.get("SPEECH_KEY")
        speech_region = os.environ.get("SPEECH_REGION")

        university_system = UniversitySystem(
            anthropic_api_key=anthropic_key,
            elevenlabs_api_key=elevenlabs_key,
            google_api_key=google_key,
            openai_api_key=openai_key,
            speech_key=speech_key,
            speech_region=speech_region,
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
@click.option("--professor-id", "-p", help="Specify professor ID (creates new if not specified)")
@click.option("--weeks", default=14, type=int, help="Number of weeks")
@click.option("--lectures-per-week", default=1, type=int, help="Lectures per week")
@click.option("--description", help="Course description (auto-generated if not provided)")
def create_course(department, title, code, professor_id, weeks, lectures_per_week, description):
    """Create a new course."""
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
            task = progress.add_task("Creating course...", total=None)

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
def list_professors():
    """List all professors."""
    try:
        system = get_system()
        professors = system.repository.professor.list()

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
@click.option("--specialization", "-s", help="Specialization (AI-generated if not provided)")
@click.option("--gender", "-g", help="Gender (AI-generated if not provided)")
@click.option("--accent", "-a", help="Accent (AI-generated if not provided)")
@click.option("--age", type=int, help="Age (AI-generated if not provided)")
@click.option("--title", "-t", help="Academic title (AI-generated if not provided)")
@click.option("--background", "-b", help="Background (AI-generated if not provided)")
def create_professor(name, department, specialization, gender, accent, age, title, background):
    """Create a new professor with AI-generated attributes."""
    try:
        system = get_system()

        console.print(
            Panel(
                f"Creating professor with AI" f"{f': [bold]{name}[/bold]' if name else ''}",
                subtitle=(
                    f"{department or 'AI-generated dept.'} - "
                    f"{specialization or 'AI-generated spec.'}"
                ),
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
                subtitle=f"{course_code or 'All courses'}" + (f" - {model} model" if model else ""),
            )
        )
        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing lectures:[/red] {str(e)}")


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
@click.option("--week", "-w", required=True, type=int, help="Week number")
@click.option("--number", "-n", default=1, type=int, help="Lecture number within the week")
def play_lecture(course_code, week, number):
    """Play audio for an existing lecture."""
    try:
        system = get_system()

        # Check if lecture exists
        lectures = system.get_lecture_preview(course_code=course_code)
        lecture = next(
            (
                lecture_preview
                for lecture_preview in lectures
                if lecture_preview["course_code"] == course_code
                and lecture_preview["week"] == week
                and lecture_preview["number"] == number
            ),
            None,
        )

        if not lecture:
            console.print(
                f"[red]Error:[/red] Lecture not found for "
                f"{course_code}, Week {week}, Number {number}"
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
        traceback.print_exc()


@cli.command()
@click.option("--course-code", "-c", required=True, help="Course code")
@click.option("--week", "-w", required=True, type=int, help="Week number")
@click.option("--number", "-n", default=1, type=int, help="Lecture number within the week")
def show_lecture(course_code, week, number):
    """Display a generated lecture content."""
    try:
        system = get_system()
        course = system.repository.course.get_by_code(course_code)
        if not course:
            console.print(f"[red]Error:[/red] Course {course_code} not found")
            return

        # Get the lecture
        lecture = system.repository.lecture.get_by_course_week_order(
            course_id=course.id, week_number=week, order_in_week=number
        )

        if not lecture:
            console.print(
                f"[red]Error:[/red] Lecture not found for "
                f"{course_code}, Week {week}, Number {number}"
            )
            console.print(
                "Try generating the lecture first with [bold]generate-lecture[/bold] command"
            )
            return

        # Display lecture content as markdown
        console.print(Markdown(lecture.content))

        # Show audio status
        if lecture.audio_url:
            console.print(f"\n[green]Audio available at URL:[/green] {lecture.audio_url}")
        else:
            console.print("\n[yellow]No audio available.[/yellow]")
            console.print("Generate audio with [bold]create-audio[/bold] command")

    except Exception as e:
        console.print(f"[red]Error displaying lecture:[/red] {str(e)}")


if __name__ == "__main__":
    cli()
