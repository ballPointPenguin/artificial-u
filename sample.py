#!/usr/bin/env python3
"""
Sample script demonstrating the ArtificialU system.

This script creates a sample course, professor, and lecture,
then converts the lecture to audio.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Set up .env file with API keys

Usage:
python sample.py
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Create samples directory if it doesn't exist
os.makedirs("samples", exist_ok=True)

# Save the sample lecture to a file
sample_lecture_path = Path("samples/sample_lecture.md")
if not sample_lecture_path.exists():
    # This would typically come from the artifact we created
    sample_lecture = """
# Introduction to Neural Networks
## CSCI-4512: Advanced Artificial Intelligence
### Dr. Mikhail Volkov, Week 3, Lecture 1

*[Professor Volkov enters the lecture hall wearing his characteristic bow tie, today in a deep burgundy color that matches his pocket square. He adjusts his glasses and surveys the room with a slight smile beneath his salt-and-pepper mustache.]*

Good morning, everyone. Last week we explored the foundations of machine learning—supervised and unsupervised approaches, the bias-variance tradeoff, and evaluation metrics. Today, we begin our journey into what is perhaps the most transformative domain in modern artificial intelligence: neural networks.

[... rest of lecture content ...]
    """

    with open(sample_lecture_path, "w") as f:
        f.write(sample_lecture)

# Load environment variables from .env file
load_dotenv()

console = Console()


def main():
    """Run the demonstration."""
    console.print(
        Panel("ArtificialU Demonstration", subtitle="AI-powered university lectures")
    )

    # Check for API keys
    missing_vars = []
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")

    if not anthropic_api_key:
        missing_vars.append("ANTHROPIC_API_KEY")
    if not elevenlabs_api_key:
        missing_vars.append("ELEVENLABS_API_KEY")

    if missing_vars:
        console.print("[red]Error:[/red] Missing required environment variables:")
        for var in missing_vars:
            console.print(f"  - {var}")
        console.print(
            "\
Please set these in a .env file or environment variables before running."
        )
        return

    console.print("[bold]Step 1:[/bold] Initializing system...")

    # In a full implementation, we would import and use the UniversitySystem class
    # For demonstration, we'll simulate the process with delays

    time.sleep(1)
    console.print("[green]✓[/green] System initialized")

    console.print(
        "\
[bold]Step 2:[/bold] Creating professor..."
    )
    time.sleep(2)
    console.print("[green]✓[/green] Created professor: [bold]Dr. Mikhail Volkov[/bold]")
    console.print("   Department: Computer Science")
    console.print("   Specialization: Artificial Intelligence")
    console.print(
        "   Background: 58-year-old Russian-American with background at Moscow State University and Bell Labs"
    )

    console.print(
        "\
[bold]Step 3:[/bold] Creating course..."
    )
    time.sleep(2)
    console.print(
        "[green]✓[/green] Created course: [bold]Advanced Artificial Intelligence[/bold]"
    )
    console.print("   Code: CSCI-4512")
    console.print("   Level: Graduate")
    console.print("   Weeks: 14")
    console.print("   Lectures per week: 2")

    console.print(
        "\
[bold]Step 4:[/bold] Generating lecture..."
    )
    time.sleep(3)
    console.print(
        "[green]✓[/green] Generated lecture: [bold]Introduction to Neural Networks[/bold]"
    )
    console.print("   Week: 3, Lecture: 1")
    console.print("   Length: ~3000 words")

    console.print(
        "\
[bold]Step 5:[/bold] Converting lecture to audio..."
    )
    time.sleep(3)
    console.print("[green]✓[/green] Created audio file")
    console.print(
        "   Saved to: [italic]audio_files/CSCI-4512/week3/lecture1.mp3[/italic]"
    )
    console.print("   Duration: ~25 minutes")

    console.print(
        "\
[bold]Demonstration complete![/bold]"
    )
    console.print(
        "\
In a full implementation, you would be able to:"
    )
    console.print("- Browse courses and professors through the CLI or web interface")
    console.print("- Generate new lectures on demand")
    console.print("- Listen to lectures through an integrated player")
    console.print("- Ask questions to professors during virtual 'office hours'")

    # Show a preview of the lecture content
    console.print(
        "\
[bold]Lecture Preview:[/bold]"
    )

    try:
        with open(sample_lecture_path, "r") as f:
            lecture_content = f.read()
            # Show just the first few paragraphs
            preview = "\
".join(
                lecture_content.split(
                    "\
"
                )[:15]
            )
            console.print(
                Markdown(
                    preview
                    + "\
\
[... content continues ...]"
                )
            )
    except Exception as e:
        console.print(f"[red]Error reading sample lecture:[/red] {e}")


if __name__ == "__main__":
    main()
