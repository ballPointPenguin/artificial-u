"""Unit tests for the ImageService fallback, sanitization, and resilience mechanisms."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.services.image_service import (
    ImageGenerationResult,
    ImageService,
    _sanitize_safety_keywords,
)


class MockProfessor:
    """Mock helper class for testing image prompts and attributes."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_sanitize_safety_keywords():
    """Verify that sensitive historical words are successfully replaced with mild academic equivalents."""
    text = "The course discusses slavery in the colonies, violent rebellions, and bloody battles."
    sanitized = _sanitize_safety_keywords(text)

    # Assert replacements occurred
    assert "slavery" not in sanitized.lower()
    assert "historical servitude" in sanitized.lower()

    assert "colonies" not in sanitized.lower()
    assert "settlements" in sanitized.lower()

    assert "violent" not in sanitized.lower()
    assert "turbulent" in sanitized.lower()

    assert "rebellions" not in sanitized.lower()
    assert "resistance movements" in sanitized.lower()

    assert "bloody" not in sanitized.lower()
    assert "battles" not in sanitized.lower()
    assert "clashes" in sanitized.lower()


@pytest.mark.asyncio
async def test_generate_lecture_slide_image_progressive_retries(monkeypatch):
    """Test that generate_lecture_slide_image progressively drops references and sanitizes on errors."""
    storage_service = MagicMock()
    storage_service.images_bucket = "images"
    storage_service.generate_lecture_image_key.return_value = "CS101/slide_10.png"
    storage_service.upload_file = AsyncMock(
        return_value=(True, "https://storage.example/slide_10.png")
    )

    image_service = ImageService(storage_service=storage_service)

    # Mock _generate_with_backend to fail on the first six attempts and succeed on the seventh (gpt-image-2 fallback)
    mock_generate = AsyncMock()
    mock_generate.side_effect = [
        Exception("Attempt 1 failure"),
        Exception("Attempt 2 failure"),
        Exception("Attempt 3 failure"),
        Exception("Attempt 4 failure"),
        Exception("Attempt 5 failure"),
        Exception("Attempt 6 failure"),
        [b"fake_openai_bytes"],  # Success (Attempt 7 - gpt-image-2 fallback)
    ]
    monkeypatch.setattr(image_service, "_generate_with_backend", mock_generate)
    monkeypatch.setattr(image_service, "_log_image_prompt", AsyncMock())
    monkeypatch.setattr(image_service.settings, "OPENAI_API_KEY", "test-key")

    professor = MockProfessor(
        name="Dr. Sarah Chen",
        gender="Female",
        age=45,
        title="Professor of Quantum Computing",
        description="Tall with short dark hair, often wears professional attire",
        specialization="Quantum Computing",
        image_url="https://example.com/prof.png",
    )
    course = MockProfessor(
        code="CS101",
        title="Intro to Computing",
    )

    url = await image_service.generate_lecture_slide_image(
        professor=professor,
        course=course,
        week_number=1,
        lecture_order=1,
        lecture_summary="Slavery and colonialism in 18th century America.",
        chunk_text="A slide about colonizing settlements and slave rebellions.",
        slot_idx=10,
        previous_chunk_text="Previously, we discussed settlements.",
        first_slide_url="https://example.com/first.png",
        previous_slide_url="https://example.com/prev.png",
        aspect_ratio="1:1",
    )

    # Check that we ultimately got a valid slide URL from the gpt-image-2 fallback
    assert url == "https://storage.example/slide_10.png"

    # Assert _generate_with_backend was called exactly 7 times (since the 7th fallback succeeded)
    assert mock_generate.call_count == 7

    # Verify properties of Attempt 1: Full references, no sanitization, gemini-3.1-flash-lite-image
    first_call = mock_generate.call_args_list[0]
    first_kw = first_call[1]
    assert first_kw["model_name"] == "gemini-3.1-flash-lite-image"
    assert first_kw["reference_image_urls"] == [
        "https://example.com/prof.png",
        "https://example.com/first.png",
        "https://example.com/prev.png",
    ]
    assert "Slavery and colonialism" in first_kw["prompt"]

    # Verify properties of Attempt 7: No references, sanitized text, gpt-image-2 fallback
    last_call = mock_generate.call_args_list[6]
    last_kw = last_call[1]
    assert last_kw["model_name"] == "gpt-image-2"
    assert last_kw["reference_image_urls"] is None  # OpenAI backend gets None reference_image_urls
    assert "historical servitude and historical territorial settlement" in last_kw["prompt"]


class MockCourse:
    """Mock helper class for testing course image prompts and attributes."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.asyncio
async def test_generate_course_image_retries_with_sanitized_text_on_safety_block(monkeypatch):
    """
    A course whose description trips Gemini's safety filter should surface as a
    "no image data" failure on the first attempt, then succeed once the prompt
    text is sanitized on the second attempt (same model).
    """
    storage_service = MagicMock()
    storage_service.images_bucket = "images"

    image_service = ImageService(storage_service=storage_service)
    assert image_service.model_name == "gemini-3.1-flash-lite-image"

    no_image_result = ImageGenerationResult(
        success=False,
        error=MagicMock(error_type=MagicMock(value="backend_unavailable")),
    )
    success_result = ImageGenerationResult(success=True, image_keys=["course_art.png"])

    mock_generate_image = AsyncMock(side_effect=[no_image_result, success_result])
    monkeypatch.setattr(image_service, "generate_image", mock_generate_image)

    course = MockCourse(
        id=100,
        code="HIST201",
        title="The Age of Rebellion",
        description="A survey of slavery, colonization, and violent uprisings.",
        level="Undergraduate",
    )

    result = await image_service.generate_course_image(course=course, aspect_ratio="1:1")

    assert result.success is True
    assert result.image_keys == ["course_art.png"]
    assert mock_generate_image.call_count == 2

    # Attempt 1: original text, primary model
    first_kw = mock_generate_image.call_args_list[0][1]
    assert first_kw["model_name_override"] == "gemini-3.1-flash-lite-image"
    assert "slavery" in first_kw["prompt"].lower()

    # Attempt 2: sanitized text, same primary model
    second_kw = mock_generate_image.call_args_list[1][1]
    assert second_kw["model_name_override"] == "gemini-3.1-flash-lite-image"
    assert "slavery" not in second_kw["prompt"].lower()
    assert "historical servitude" in second_kw["prompt"].lower()


@pytest.mark.asyncio
async def test_generate_course_image_falls_back_to_alternate_model_and_openai(monkeypatch):
    """
    If sanitized text still fails on the primary model, fall back to the sibling
    Gemini model, and finally to OpenAI's gpt-image-2 as a last resort.
    """
    storage_service = MagicMock()
    storage_service.images_bucket = "images"

    image_service = ImageService(storage_service=storage_service)
    monkeypatch.setattr(image_service.settings, "OPENAI_API_KEY", "test-key")

    no_image_result = ImageGenerationResult(
        success=False,
        error=MagicMock(error_type=MagicMock(value="backend_unavailable")),
    )
    success_result = ImageGenerationResult(success=True, image_keys=["course_art.png"])

    mock_generate_image = AsyncMock(
        side_effect=[no_image_result, no_image_result, no_image_result, success_result]
    )
    monkeypatch.setattr(image_service, "generate_image", mock_generate_image)

    course = MockCourse(
        id=101,
        code="HIST202",
        title="Empires and Conquest",
        description="A study of war, conquest, and rebellion.",
        level="Graduate",
    )

    result = await image_service.generate_course_image(course=course, aspect_ratio="1:1")

    assert result.success is True
    assert mock_generate_image.call_count == 4

    models_used = [
        call.kwargs["model_name_override"] for call in mock_generate_image.call_args_list
    ]
    assert models_used == [
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-image",
        "gpt-image-2",
    ]


@pytest.mark.asyncio
async def test_generate_course_image_returns_last_failure_when_all_attempts_fail(monkeypatch):
    """If every attempt fails, the last failed result should be returned (not raised)."""
    storage_service = MagicMock()
    storage_service.images_bucket = "images"

    image_service = ImageService(storage_service=storage_service)
    monkeypatch.setattr(image_service.settings, "OPENAI_API_KEY", None)

    failing_error = MagicMock(error_type=MagicMock(value="backend_unavailable"))
    failing_result = ImageGenerationResult(success=False, error=failing_error)

    mock_generate_image = AsyncMock(return_value=failing_result)
    monkeypatch.setattr(image_service, "generate_image", mock_generate_image)

    course = MockCourse(
        id=102,
        code="HIST203",
        title="A Course",
        description="Some description.",
        level="Graduate",
    )

    result = await image_service.generate_course_image(course=course, aspect_ratio="1:1")

    assert result.success is False
    assert result.error is failing_error
    # No OpenAI key configured: original + sanitized on primary model, plus one
    # sanitized attempt on the sibling Gemini model.
    assert mock_generate_image.call_count == 3
    models_used = [
        call.kwargs["model_name_override"] for call in mock_generate_image.call_args_list
    ]
    assert models_used == [
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-image",
    ]


@pytest.mark.asyncio
async def test_generate_professor_image_retries_with_sanitized_text_on_safety_block(monkeypatch):
    """
    A professor bio that trips Gemini's safety filter should surface as a
    "no image data" failure on the first attempt, then succeed once the prompt
    text is sanitized on the second attempt (same model).
    """
    storage_service = MagicMock()
    storage_service.images_bucket = "images"

    image_service = ImageService(storage_service=storage_service)
    assert image_service.model_name == "gemini-3.1-flash-lite-image"

    no_image_result = ImageGenerationResult(
        success=False,
        error=MagicMock(error_type=MagicMock(value="backend_unavailable")),
    )
    success_result = ImageGenerationResult(success=True, image_keys=["professor.png"])

    mock_generate_image = AsyncMock(side_effect=[no_image_result, success_result])
    monkeypatch.setattr(image_service, "generate_image", mock_generate_image)

    professor = MockProfessor(
        id=50,
        name="Dr. Marcus Webb",
        gender="Male",
        age=58,
        description="A weathered military historian who studies war and rebellion.",
        specialization="War and colonial conquest",
    )

    result = await image_service.generate_professor_image(professor, aspect_ratio="1:1")

    assert result.success is True
    assert result.image_keys == ["professor.png"]
    assert mock_generate_image.call_count == 2

    # Attempt 1: original text, primary model
    first_kw = mock_generate_image.call_args_list[0][1]
    assert first_kw["model_name_override"] == "gemini-3.1-flash-lite-image"
    assert "war" in first_kw["prompt"].lower()

    # Attempt 2: sanitized text, same primary model
    second_kw = mock_generate_image.call_args_list[1][1]
    assert second_kw["model_name_override"] == "gemini-3.1-flash-lite-image"
    assert "war" not in second_kw["prompt"].lower()
    assert "historical conflict" in second_kw["prompt"].lower()


@pytest.mark.asyncio
async def test_generate_professor_image_falls_back_to_alternate_model_and_openai(monkeypatch):
    """
    If sanitized text still fails on the primary model, fall back to the sibling
    Gemini model, and finally to OpenAI's gpt-image-2 as a last resort.
    """
    storage_service = MagicMock()
    storage_service.images_bucket = "images"

    image_service = ImageService(storage_service=storage_service)
    monkeypatch.setattr(image_service.settings, "OPENAI_API_KEY", "test-key")

    no_image_result = ImageGenerationResult(
        success=False,
        error=MagicMock(error_type=MagicMock(value="backend_unavailable")),
    )
    success_result = ImageGenerationResult(success=True, image_keys=["professor.png"])

    mock_generate_image = AsyncMock(
        side_effect=[no_image_result, no_image_result, no_image_result, success_result]
    )
    monkeypatch.setattr(image_service, "generate_image", mock_generate_image)

    professor = MockProfessor(
        id=51,
        name="Dr. Elena Vasquez",
        gender="Female",
        age=49,
        description="An expert on rebellion and armed conflict.",
        specialization="Revolutionary movements",
    )

    result = await image_service.generate_professor_image(professor, aspect_ratio="1:1")

    assert result.success is True
    assert mock_generate_image.call_count == 4

    models_used = [
        call.kwargs["model_name_override"] for call in mock_generate_image.call_args_list
    ]
    assert models_used == [
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-image",
        "gpt-image-2",
    ]


@pytest.mark.asyncio
async def test_generate_professor_image_returns_last_failure_when_all_attempts_fail(monkeypatch):
    """If every attempt fails, the last failed result should be returned (not raised)."""
    storage_service = MagicMock()
    storage_service.images_bucket = "images"

    image_service = ImageService(storage_service=storage_service)
    monkeypatch.setattr(image_service.settings, "OPENAI_API_KEY", None)

    failing_error = MagicMock(error_type=MagicMock(value="backend_unavailable"))
    failing_result = ImageGenerationResult(success=False, error=failing_error)

    mock_generate_image = AsyncMock(return_value=failing_result)
    monkeypatch.setattr(image_service, "generate_image", mock_generate_image)

    professor = MockProfessor(
        id=52,
        name="Dr. Sam Lee",
        description="Some description.",
        specialization="Some field.",
    )

    result = await image_service.generate_professor_image(professor, aspect_ratio="1:1")

    assert result.success is False
    assert result.error is failing_error
    # No OpenAI key configured: original + sanitized on primary model, plus one
    # sanitized attempt on the sibling Gemini model.
    assert mock_generate_image.call_count == 3
    models_used = [
        call.kwargs["model_name_override"] for call in mock_generate_image.call_args_list
    ]
    assert models_used == [
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-image",
    ]
