"""Unit tests for the ImageService fallback, sanitization, and resilience mechanisms."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.services.image_service import ImageService, _sanitize_safety_keywords


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
