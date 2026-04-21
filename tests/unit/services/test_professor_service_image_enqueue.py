from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Professor
from artificial_u.services.professor_service import ProfessorService


@pytest.mark.unit
def test_create_professor_enqueues_image_job_when_missing_image_url():
    repository_factory = MagicMock()
    voice_service = MagicMock()
    job_enqueue_service = MagicMock()

    # VoiceService is expected to be called, but may mutate professor in place in real impl.
    voice_service.select_voice_for_professor.return_value = {"db_voice_id": 7, "name": "Test Voice"}

    saved = Professor(id=123, name="Dr. Enqueue", image_url=None)
    repository_factory.professor.create.return_value = saved

    service = ProfessorService(
        repository_factory=repository_factory,
        voice_service=voice_service,
        job_enqueue_service=job_enqueue_service,
    )

    created = service.create_professor(Professor(name="Dr. Enqueue"))

    assert created.id == 123
    job_enqueue_service.enqueue_professor_image_generation.assert_called_once_with(123)


@pytest.mark.unit
def test_create_professor_does_not_enqueue_image_job_when_image_url_present():
    repository_factory = MagicMock()
    voice_service = MagicMock()
    job_enqueue_service = MagicMock()

    saved = Professor(id=456, name="Dr. Has Image", image_url="https://example.com/p.jpg")
    repository_factory.professor.create.return_value = saved

    service = ProfessorService(
        repository_factory=repository_factory,
        voice_service=voice_service,
        job_enqueue_service=job_enqueue_service,
    )

    created = service.create_professor(Professor(name="Dr. Has Image", image_url=saved.image_url))

    assert created.id == 456
    job_enqueue_service.enqueue_professor_image_generation.assert_not_called()
