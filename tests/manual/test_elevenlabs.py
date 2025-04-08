"""
Manual test suite for ElevenLabs integration with ArtificialU.

This module tests:
1. Creating custom voices for professors
2. Converting a lecture to speech
3. Saving the audio file

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Get an API key from ElevenLabs

Usage:
    # Run with API key:
    ELEVENLABS_API_KEY=<your_key> pytest tests/manual/test_elevenlabs.py -v

    # Run with API key and custom paths:
    ELEVENLABS_API_KEY=<your_key> DATABASE_PATH=custom.db pytest tests/manual/test_elevenlabs.py -v
"""

import os
import re
from pathlib import Path
import pytest
from rich.console import Console
from dotenv import load_dotenv

from artificial_u.audio.processor import AudioProcessor
from artificial_u.models.core import Professor, Lecture

console = Console()

# Load .env.test for non-sensitive configuration (DATABASE_PATH, etc.)
# load_dotenv(".env.test")

# Skip all tests if no API key in environment
# Note: We check environ directly, not get(), because we don't want to fall back to .env.test
pytestmark = pytest.mark.skipif(
    "ELEVENLABS_API_KEY" not in os.environ,
    reason="ELEVENLABS_API_KEY not found in environment (don't use .env.test for API keys)",
)


@pytest.fixture(scope="module")
def audio_processor():
    """Initialize AudioProcessor with API key."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    return AudioProcessor(api_key=api_key)


@pytest.fixture(scope="module")
def test_professors():
    """Create test professor profiles."""
    return [
        Professor(
            id="prof_volkov",
            name="Dr. Mikhail Volkov",
            title="Professor of Computer Science",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="58-year-old Russian-American computer scientist with background at Moscow State University and Bell Labs",
            personality="Methodical, philosophical, occasional dry humor",
            teaching_style="Combines methodical explanations with philosophical perspectives",
            voice_settings={},
        ),
        Professor(
            id="prof_sharma",
            name="Dr. Priya Sharma",
            title="Assistant Professor of Statistics",
            department="Statistics",
            specialization="Probability Theory",
            background="Young woman from South Asia. PhD from MIT (recent). Worked at Google Research.",
            personality="Enthusiastic, energetic, approachable",
            teaching_style="Uses clear analogies and visual aids to explain complex concepts",
            voice_settings={},
        ),
        Professor(
            id="prof_bennett",
            name="Dr. Julian Bennett",
            title="Associate Professor of Mathematics",
            department="Mathematics",
            specialization="Linear Algebra",
            background="Middle-aged British mathematician with a background in pure and applied mathematics",
            personality="Precise, thoughtful, occasionally witty",
            teaching_style="Traditional academic with a focus on mathematical rigor",
            voice_settings={},
        ),
        Professor(
            id="prof_montgomery",
            name="Dr. Lillian Montgomery",
            title="Professor of Physics",
            department="Physics",
            specialization="Quantum Information Science",
            background="British female quantum physicist with silver-streaked black hair and piercing green eyes",
            personality="Energetic, passionate about quantum physics, encouraging",
            teaching_style="Connects abstract concepts to practical applications with vivid metaphors",
            voice_settings={},
        ),
    ]


@pytest.fixture
def sample_lecture(request):
    """Load a sample lecture for a specific professor."""

    def _get_lecture(professor_id: str) -> Lecture:
        # Map professor IDs to sample lecture files
        lecture_files = {
            "prof_volkov": "samples/sample_lecture.md",
            "prof_sharma": "samples/statistical_learning_theory_lecture.md",
            "prof_bennett": "samples/tensors-lecture.md",
            "prof_montgomery": "samples/quantum_computing_lecture.md",
        }

        if professor_id not in lecture_files:
            raise ValueError(
                f"No sample lecture available for professor ID: {professor_id}"
            )

        file_path = lecture_files[professor_id]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Lecture file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from lecture content
        title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
        title = title_match.group(1) if title_match else "Sample Lecture"

        return Lecture(
            id=f"lecture_{professor_id}",
            title=title,
            course_id=f"course_{professor_id}",
            week_number=1,
            order_in_week=1,
            description=f"Sample lecture by professor {professor_id}",
            content=content,
        )

    return _get_lecture


@pytest.mark.manual
def test_subscription_info(audio_processor):
    """Test retrieving ElevenLabs subscription information."""
    subscription_info = audio_processor.get_user_subscription_info()
    assert subscription_info is not None

    # Log subscription details
    console.print("\n[bold]Subscription Info:[/bold]")
    console.print(
        f"Available characters: {subscription_info.get('available_characters', 'Unknown')}"
    )
    console.print(f"Voice limit: {subscription_info.get('voice_limit', 'Unknown')}")
    console.print(f"Voice count: {subscription_info.get('voice_count', 'Unknown')}")


@pytest.mark.manual
def test_available_voices(audio_processor):
    """Test retrieving available voices from ElevenLabs."""
    voices = audio_processor.get_available_voices()
    assert voices is not None
    assert len(voices) > 0

    console.print(f"\n[bold]Available Voices:[/bold] Found {len(voices)} voices")


@pytest.mark.manual
@pytest.mark.parametrize("professor_id", ["prof_volkov", "prof_sharma"])
def test_voice_creation(audio_processor, test_professors, professor_id):
    """Test creating/selecting voices for professors."""
    professor = next(p for p in test_professors if p.id == professor_id)

    # Create/select voice
    voice_id = audio_processor.create_professor_voice(professor)
    assert voice_id is not None
    console.print(f"\nCreated voice for {professor.name}: {voice_id}")

    # Get full voice object
    voice = audio_processor.get_voice_for_professor(professor)
    assert voice is not None


@pytest.mark.manual
def test_text_to_speech(audio_processor, test_professors, sample_lecture):
    """Test converting a lecture to speech."""
    professor_id = "prof_volkov"  # Using one professor for this test
    professor = next(p for p in test_professors if p.id == professor_id)
    lecture = sample_lecture(professor_id)

    # Convert to speech
    audio_path, audio_data = audio_processor.text_to_speech(lecture, professor)

    assert audio_path is not None
    assert audio_data is not None
    assert os.path.exists(audio_path)

    # Log results
    console.print(f"\n[bold]Text-to-Speech Results:[/bold]")
    console.print(f"Audio file saved to: {audio_path}")
    console.print(f"Audio size: {len(audio_data) / (1024 * 1024):.2f} MB")


@pytest.mark.manual
def test_voice_consistency(audio_processor, test_professors, sample_lecture):
    """Test voice consistency across multiple generations."""
    professor_id = "prof_volkov"
    professor = next(p for p in test_professors if p.id == professor_id)
    lecture = sample_lecture(professor_id)

    # Generate two samples with the same voice
    audio_path1, audio_data1 = audio_processor.text_to_speech(lecture, professor)
    audio_path2, audio_data2 = audio_processor.text_to_speech(lecture, professor)

    assert audio_path1 != audio_path2  # Should be different files
    assert len(audio_data1) > 0 and len(audio_data2) > 0  # Both should have content

    console.print("\n[bold]Voice Consistency Test:[/bold]")
    console.print(f"Sample 1: {audio_path1}")
    console.print(f"Sample 2: {audio_path2}")
