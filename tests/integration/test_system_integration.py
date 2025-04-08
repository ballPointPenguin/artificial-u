"""
Integration tests for the UniversitySystem using Ollama for local testing.
"""

import os
import pytest
import tempfile
from pathlib import Path

from artificial_u.system import UniversitySystem
from artificial_u.models.core import Professor, Course, Lecture

# Skip these tests if Ollama is not installed or not running
ollama_installed = True
try:
    import ollama

    # Try to list models to check if Ollama server is running
    try:
        ollama.list()
        ollama_running = True
    except Exception:
        ollama_running = False
except ImportError:
    ollama_installed = False
    ollama_running = False

# Condition to skip tests
requires_ollama = pytest.mark.skipif(
    not (ollama_installed and ollama_running),
    reason="Ollama not installed or not running",
)

# Check if the tinyllama model is available
has_tinyllama = False
if ollama_running:
    models_data = ollama.list()
    model_names = [model.model for model in models_data.models]
    has_tinyllama = any("tinyllama" in model_name for model_name in model_names)
    print(f"Available models: {model_names}")
    print(f"Has TinyLlama: {has_tinyllama}")

# Skip if tinyllama is not available
requires_tinyllama = pytest.mark.skipif(
    not has_tinyllama,
    reason="TinyLlama model not available, run 'ollama pull tinyllama'",
)


@pytest.fixture
def test_system():
    """Create a test system using Ollama for content generation."""
    # Create temporary directories for database and audio
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_db.db")
        audio_path = os.path.join(temp_dir, "audio")

        # Create the system
        system = UniversitySystem(
            content_backend="ollama",
            content_model="tinyllama",
            db_path=db_path,
            audio_path=audio_path,
            # Use dummy API keys since we're skipping audio generation
            anthropic_api_key="sk_not_needed_for_test",
            elevenlabs_api_key="el_not_needed_for_test",
        )

        # Monkey patch the audio_processor.text_to_speech method to skip actual API calls
        def mock_text_to_speech(lecture, professor):
            audio_path = os.path.join(audio_path, f"{lecture.id}.mp3")
            # Create an empty file
            with open(audio_path, "wb") as f:
                f.write(b"mock audio data")
            return audio_path, b"mock audio data"

        system.audio_processor.text_to_speech = mock_text_to_speech

        yield system


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
def test_create_professor_with_ollama(test_system):
    """Test creating a professor using Ollama for content generation."""
    # Create a professor
    professor = test_system.create_professor(
        name="Dr. Test Professor",
        department="Computer Science",
        specialization="Software Testing",
    )

    # Verify professor was created and stored in database
    assert professor.id is not None

    # Verify professor has voice settings
    assert professor.voice_settings is not None
    assert "voice_id" in professor.voice_settings

    # Retrieve from database to ensure it was saved
    retrieved = test_system.repository.get_professor(professor.id)
    assert retrieved is not None
    assert retrieved.name == professor.name
    assert retrieved.department == "Computer Science"


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
def test_create_course_with_ollama(test_system):
    """Test creating a course using Ollama for content generation."""
    # Create a professor first
    professor = test_system.create_professor(
        name="Dr. Course Test",
        department="Physics",
        specialization="Quantum Mechanics",
    )

    # Create a course
    course, _ = test_system.create_course(
        code="PHYS101",
        title="Introduction to Physics",
        department="Physics",
        level="Undergraduate",
        professor_id=professor.id,
        description="A first-year course covering fundamental physics concepts",
        lectures_per_week=2,
        weeks=14,
    )

    # Verify course was created and has a syllabus
    assert course.id is not None
    assert course.syllabus is not None

    # Retrieve from database
    retrieved = test_system.repository.get_course(course.id)
    assert retrieved is not None
    assert retrieved.code == "PHYS101"
    assert retrieved.professor_id == professor.id


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
def test_generate_lecture_with_ollama(test_system):
    """Test generating a lecture using Ollama."""
    # Create dependencies
    professor = test_system.create_professor(
        name="Dr. Lecture Test",
        department="Biology",
        specialization="Molecular Biology",
    )

    course, _ = test_system.create_course(
        code="BIO201",
        title="Cellular Biology",
        department="Biology",
        level="Undergraduate",
        professor_id=professor.id,
        description="Comprehensive study of cell structure and function",
        lectures_per_week=2,
        weeks=15,
    )

    # Generate a lecture
    lecture, _, _ = test_system.generate_lecture(
        course_code=course.code,
        week=1,
        number=1,
        topic="Introduction to Cell Structure",
        word_count=1500,
    )

    # Verify lecture was created
    assert lecture.id is not None
    assert lecture.content is not None
    assert len(lecture.content) > 0

    # Retrieve from database
    retrieved = test_system.repository.get_lecture(lecture.id)
    assert retrieved is not None
    assert retrieved.title == "Introduction to Cell Structure"
    assert retrieved.course_id == course.id
