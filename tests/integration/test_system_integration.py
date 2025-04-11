"""
Integration tests for the UniversitySystem using Ollama for local testing.
"""

import os
import pytest
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import uuid
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

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


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env.test file."""
    load_dotenv(".env.test")
    yield


@pytest.fixture(scope="session")
def db_available():
    """Check if the database is available."""
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )
    try:
        # Try to connect to the database
        engine = create_engine(db_url)
        with engine.connect():
            return True
    except OperationalError:
        return False
    except Exception:
        return False


@pytest.fixture
def test_system(db_available):
    """Create a test system using Ollama for content generation."""
    # Skip if the database is not available
    if not db_available:
        pytest.skip("Database not available")

    # Create temporary directory for audio
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "audio")
        os.makedirs(audio_path, exist_ok=True)

        # Get PostgreSQL URL from environment
        db_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
        )

        # Create the system
        system = UniversitySystem(
            content_backend="ollama",
            content_model="tinyllama",
            # Use dummy API keys since we're skipping audio generation
            anthropic_api_key="sk_not_needed_for_test",
            elevenlabs_api_key="el_not_needed_for_test",
            log_level="INFO",
            db_url=db_url,
        )

        # Set a low timeout for Ollama requests to prevent hangs
        # Note: Accessing client directly might change depending on generator implementation
        if hasattr(system.content_generator, "client") and hasattr(
            system.content_generator.client, "create"
        ):
            original_create = system.content_generator.client.create

            def create_with_timeout(*args, **kwargs):
                return original_create(
                    *args, **kwargs, timeout=15  # Use 15 second timeout for tests
                )

            system.content_generator.client.create = create_with_timeout
        else:
            # Fallback if client structure changes
            print(
                "Warning: Could not set Ollama timeout for tests due to changed client structure."
            )

        # Add voice_service to professor_service
        # This is a workaround for the test since the UniversitySystem
        # doesn't connect them in the current implementation
        system.professor_service.voice_service = system.voice_service

        # Mock the voice selection to always return a fixed voice ID
        def mock_select_voice_for_professor(professor, **kwargs):
            return {
                "voice_id": "test_voice_id",
                "stability": 0.5,
                "clarity": 0.8,
            }

        system.voice_service.select_voice_for_professor = (
            mock_select_voice_for_professor
        )

        # Monkey patch the tts_service.generate_audio method to skip actual API calls
        def mock_generate_audio(
            text, voice_id, stability=None, clarity=None, style=None
        ):
            # Return mock audio data
            return b"mock audio data"

        system.tts_service.generate_audio = mock_generate_audio

        # Monkey patch audio_service.create_lecture_audio to skip actual processing
        def mock_create_lecture_audio(
            lecture_id=None, course_code=None, week=None, number=None
        ):
            if lecture_id:
                lecture = system.repository.get_lecture(lecture_id)
            else:
                course = system.repository.get_course_by_code(course_code)
                lecture = system.repository.get_lecture_by_course_week_order(
                    course.id, week, number
                )

            professor = system.repository.get_professor(lecture.professor_id)
            # Define audio_url, not audio_path
            audio_url = f"mock_storage://{course_code}/week{week}/lecture{number}.mp3"

            # Update lecture with audio url
            lecture_to_update = system.repository.get_lecture(lecture.id)
            lecture_to_update.audio_url = audio_url  # Use audio_url
            updated_lecture = system.repository.update_lecture(lecture_to_update)
            return audio_url, updated_lecture

        system.audio_service.create_lecture_audio = mock_create_lecture_audio

        yield system


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
@pytest.mark.requires_db
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
@pytest.mark.requires_db
def test_create_course_with_ollama(test_system):
    """Test creating a course using Ollama for content generation."""
    # Create a professor first
    print("TEST: Creating professor for course test...")
    professor = test_system.create_professor(
        name="Dr. Course Test",
        department="Physics",
        specialization="Quantum Mechanics",
    )
    print(f"TEST: Professor created with ID: {professor.id}")

    # Create a course with a unique code
    unique_code = f"PHY{uuid.uuid4().hex[:4].upper()}"

    print(f"TEST: Creating course with code {unique_code}...")
    course, _ = test_system.create_course(
        code=unique_code,
        title="Introduction to Physics",
        department="Physics",
        level="Undergraduate",
        professor_id=professor.id,
        description="A first-year course covering fundamental physics concepts",
        lectures_per_week=2,
        weeks=14,
    )
    print(f"TEST: Course created with ID: {course.id}")

    # Verify course was created and stored in database
    assert course.id is not None
    assert course.code == unique_code

    # Retrieve from database to ensure it was saved
    retrieved = test_system.repository.get_course(course.id)
    assert retrieved is not None
    assert retrieved.title == "Introduction to Physics"
    assert retrieved.department == "Physics"
    assert retrieved.professor_id == professor.id


@requires_ollama
@requires_tinyllama
@pytest.mark.integration
@pytest.mark.requires_db
def test_generate_lecture_with_ollama(test_system):
    """Test generating a lecture using Ollama."""
    # Create dependencies
    print("TEST: Creating professor for lecture test...")
    professor = test_system.create_professor(
        name="Dr. Lecture Test",
        department="Biology",
        specialization="Molecular Biology",
    )
    print(f"TEST: Professor created with ID: {professor.id}")

    # Create a course with a unique code
    unique_code = f"BIO{uuid.uuid4().hex[:4].upper()}"

    print(f"TEST: Creating course with code {unique_code}...")
    course, _ = test_system.create_course(
        code=unique_code,
        title="Cellular Biology",
        department="Biology",
        level="Undergraduate",
        professor_id=professor.id,
        description="Comprehensive study of cell structure and function",
        lectures_per_week=2,
        weeks=15,
    )
    print(f"TEST: Course created with ID: {course.id}")

    # Generate a lecture
    print("TEST: Generating lecture...")
    lecture, _, _ = test_system.generate_lecture(
        course_code=course.code,
        week=1,
        number=1,
        topic="Introduction to Cell Structure",
        word_count=500,
    )
    print(f"TEST: Lecture generated with ID: {lecture.id}")

    # Verify lecture was created
    assert lecture.id is not None
    assert lecture.content is not None
    assert len(lecture.content) > 0

    # Retrieve from database
    print("TEST: Retrieving lecture from database...")
    retrieved = test_system.repository.get_lecture(lecture.id)
    assert retrieved is not None
    # Check that the title exists and is a string but don't check the exact value
    # since we can't predict what the model will return
    assert isinstance(retrieved.title, str)
    assert len(retrieved.title) > 0
    assert "Introduction to Cell Structure" in retrieved.description
    print("TEST: Lecture test completed successfully")
