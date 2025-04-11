"""
Simplified test suite for ElevenLabs integration with ArtificialU.

This module provides a single, focused test for validating the ElevenLabs
integration with the minimal API functionality needed for the MVP.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Get an API key from ElevenLabs

Usage:
    # Run with API key:
    ELEVENLABS_API_KEY=<your_key> python tests/manual/test_elevenlabs_simple.py

    # Or run with pytest:
    ELEVENLABS_API_KEY=<your_key> pytest tests/manual/test_elevenlabs_simple.py -v
"""

import os
import re
import sys
import time
import pytest
from pathlib import Path
from rich.console import Console

# Add the project root to the Python path if running directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent.parent))

# Import with the new module structure
from artificial_u.audio.processor import AudioProcessor
from artificial_u.models.core import Professor, Lecture

console = Console()

# Check if we have a real API key, not a test one
api_key = os.environ.get("ELEVENLABS_API_KEY")
using_test_key = api_key == "test_elevenlabs_key"

if api_key and not using_test_key:
    console.print("[bold green]Using real ElevenLabs API key[/bold green]")
    console.print(
        "[bold yellow]Warning: These tests will use your API quota![/bold yellow]"
    )
else:
    console.print("[bold red]No real ElevenLabs API key found[/bold red]")
    console.print(
        "These tests require a real API key set in your .env file or environment"
    )

# Skip tests if no real API key in environment
pytestmark = pytest.mark.skipif(
    not api_key or using_test_key,
    reason="Real ELEVENLABS_API_KEY not found in environment (found test key instead)",
)

# Store generated audio path as a module-level variable
_audio_path = None


@pytest.fixture(scope="module")
def audio_processor():
    """Initialize AudioProcessor with API key."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    return AudioProcessor(api_key=api_key)


@pytest.fixture(scope="module")
def test_professor():
    """Create a test professor profile."""
    return Professor(
        id=1,
        name="Dr. Ada Lovelace",
        title="Professor of Computer Science",
        department="Computer Science",
        specialization="Algorithmic Theory",
        background="Pioneering computer scientist and mathematician",
        personality="Analytical, thoughtful, and visionary",
        teaching_style="Methodical with historical context",
    )


@pytest.fixture(scope="module")
def test_lecture():
    """Create a sample lecture for testing."""
    return Lecture(
        id=1,
        title="Introduction to Computing",
        course_id=1,
        week_number=1,
        order_in_week=1,
        description="Introductory lecture on computing concepts",
        content="""
# Introduction to Computing Concepts

*[Professor enters the classroom]*

Good morning, everyone! Welcome to CS101: Introduction to Computing Concepts. 
I'm Dr. Ada Lovelace, and I'll be your guide through this fascinating field.

*[Pauses and looks around the room]*

Today, we'll be covering the fundamental concepts of computing, its history, 
and why it matters in our modern world. Let's begin by defining what we mean 
by "computing."

*[Professor speaks with enthusiasm]*

Computing refers to any goal-oriented activity requiring, benefiting from, 
or creating computers. This includes designing and building hardware and software 
systems, processing and managing information, and scientific investigations.

*[Writes key points on the board]*

The history of computing is quite interesting. While many consider it a modern field, 
the concept dates back to ancient tools like the abacus and early calculating machines.

*[Professor pauses dramatically]*

However, the formal academic field of computer science began to take shape 
in the mid-20th century, as programmable electronic computers were developed.

*[Speaks softly]*

Now, let's consider why computing is so important today...

*[Resumes normal tone]*

Any questions so far?
        """,
    )


@pytest.mark.manual
def test_api_connection(audio_processor):
    """Test basic connection to ElevenLabs API."""
    # Request available voices as a way to test connection
    voices = audio_processor.get_available_voices()

    # Verify we got a valid response
    assert isinstance(voices, list)
    assert len(voices) > 0

    # Display information about available voices
    console.print(f"\n[bold]Available Voices:[/bold] Found {len(voices)} voices")

    # Display subscription information if available
    subscription = audio_processor.get_user_subscription_info()
    if subscription:
        console.print("\n[bold]Subscription Info:[/bold]")
        console.print(
            f"Available characters: {subscription.get('available_characters', 'Unknown')}"
        )


@pytest.mark.manual
def test_text_processing(audio_processor):
    """Test text processing functionality for stage directions."""
    test_text = "[Professor enters] Good morning, everyone! [pauses] Let's begin."

    processed_text = audio_processor.process_stage_directions(test_text)

    # The processed text should be different from the original
    assert processed_text != test_text

    # Stage directions should be removed or replaced
    assert "[Professor enters]" not in processed_text
    assert "[pauses]" not in processed_text

    # A pause marker should have been added
    assert '<break time="1s"/>' in processed_text

    console.print("\n[bold]Text Processing:[/bold]")
    console.print(f"Original: {test_text}")
    console.print(f"Processed: {processed_text}")


@pytest.fixture(scope="module")
def generate_audio(audio_processor, test_professor, test_lecture):
    """Generate audio for testing and return the path."""
    global _audio_path

    if _audio_path is None:
        console.print("\n[bold]Testing Text-to-Speech:[/bold]")
        console.print(f"Converting lecture '{test_lecture.title}' to speech...")

        start_time = time.time()

        # Generate speech
        audio_path, audio_data = audio_processor.text_to_speech(
            test_lecture, test_professor
        )

        end_time = time.time()
        duration = end_time - start_time

        # Verify the results
        assert audio_path is not None
        assert audio_data is not None
        assert os.path.exists(audio_path)

        # Log results
        console.print(f"Generated audio in {duration:.2f} seconds")
        console.print(f"Audio saved to: {audio_path}")
        console.print(f"Audio size: {len(audio_data) / 1024:.2f} KB")

        _audio_path = audio_path

    return _audio_path


@pytest.mark.manual
def test_text_to_speech(generate_audio):
    """Test the full text-to-speech functionality."""
    assert generate_audio is not None
    assert os.path.exists(generate_audio)


@pytest.mark.manual
def test_play_audio(audio_processor, generate_audio):
    """Play the generated audio."""
    console.print("\n[bold]Playing Audio:[/bold]")
    console.print(f"Playing audio from {generate_audio}...")

    audio_processor.play_audio(generate_audio)
