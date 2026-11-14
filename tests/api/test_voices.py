"""Access control for the voice endpoints: professor owner or admin only."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.dependencies import ensure_student, get_repository_factory, get_voice_service
from artificial_u.models.core import Student

OWNED_BY_42 = 1
OWNED_BY_OTHER = 2
NO_OWNER = 3

VOICE = {"id": 9, "name": "Test Voice", "tts_backend": "elevenlabs", "external_id": "ext-9"}


@pytest.fixture
def voice_service():
    from artificial_u.api.app import app

    professors = {
        OWNED_BY_42: SimpleNamespace(id=OWNED_BY_42, created_by=42),
        OWNED_BY_OTHER: SimpleNamespace(id=OWNED_BY_OTHER, created_by=7),
        NO_OWNER: SimpleNamespace(id=NO_OWNER, created_by=None),
    }
    factory = MagicMock()
    factory.professor.get.side_effect = professors.get

    service = MagicMock()
    service.generate_voice_design_previews.return_value = []
    service.save_designed_voice.return_value = VOICE
    service.clone_elevenlabs_voice_to_mistral.return_value = VOICE

    app.dependency_overrides[get_repository_factory] = lambda: factory
    app.dependency_overrides[get_voice_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_repository_factory, None)
    app.dependency_overrides.pop(get_voice_service, None)


@pytest.fixture
def as_creator():
    """Make requests come from non-admin creator 42 (the client fixture defaults to an admin)."""
    from artificial_u.api.app import app

    app.dependency_overrides[ensure_student] = lambda: Student(
        id=42,
        name="Creator",
        email="creator@example.com",
        auth0_sub="creator-42",
        role="creator",
        coins=10,
        is_active=True,
    )


def _professor_requests(professor_id):
    """Every endpoint that changes or spends money on a specific professor's voice."""
    return [
        (
            f"/api/v1/voices/{professor_id}/assign_voice",
            {"external_id": "ext-9", "tts_backend": "mistral"},
        ),
        ("/api/v1/voices/design/previews", {"professor_id": professor_id}),
        (
            "/api/v1/voices/design/save",
            {
                "professor_id": professor_id,
                "generated_voice_id": "gen-1",
                "voice_name": "V",
                "voice_description": "warm, measured",
            },
        ),
        ("/api/v1/voices/clone-to-mistral", {"professor_id": professor_id}),
    ]


@pytest.mark.unit
@pytest.mark.parametrize("index", range(4))
def test_creator_can_use_voice_endpoints_for_their_own_professor(
    client: TestClient, voice_service, as_creator, index
):
    url, body = _professor_requests(OWNED_BY_42)[index]

    assert client.post(url, json=body).status_code in (200, 204)


@pytest.mark.unit
@pytest.mark.parametrize("professor_id", [OWNED_BY_OTHER, NO_OWNER])
@pytest.mark.parametrize("index", range(4))
def test_creator_is_refused_for_professors_they_do_not_own(
    client: TestClient, voice_service, as_creator, professor_id, index
):
    url, body = _professor_requests(professor_id)[index]

    assert client.post(url, json=body).status_code == 403
    voice_service.manual_voice_assignment_generic.assert_not_called()
    voice_service.generate_voice_design_previews.assert_not_called()
    voice_service.save_designed_voice.assert_not_called()
    voice_service.clone_elevenlabs_voice_to_mistral.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("professor_id", [OWNED_BY_42, OWNED_BY_OTHER, NO_OWNER])
@pytest.mark.parametrize("index", range(4))
def test_admin_can_use_voice_endpoints_for_any_professor(
    client: TestClient, voice_service, professor_id, index
):
    url, body = _professor_requests(professor_id)[index]

    assert client.post(url, json=body).status_code in (200, 204)


@pytest.mark.unit
def test_unknown_professor_is_a_404(client: TestClient, voice_service):
    response = client.post("/api/v1/voices/clone-to-mistral", json={"professor_id": 999})

    assert response.status_code == 404
    voice_service.clone_elevenlabs_voice_to_mistral.assert_not_called()


@pytest.fixture
def tts_backend(monkeypatch):
    backend = MagicMock()
    backend.text_to_speech.return_value = b"mp3-bytes"
    monkeypatch.setattr(
        "artificial_u.api.routers.voices.create_tts_backend", lambda **kwargs: backend
    )
    return backend


def _preview(client, **extra):
    return client.post(
        "/api/v1/voices/preview", json={"voice_id": "v1", "tts_backend": "mistral", **extra}
    )


@pytest.mark.unit
def test_creator_can_preview_for_their_own_professor(
    client: TestClient, voice_service, as_creator, tts_backend
):
    response = _preview(client, professor_id=OWNED_BY_42)

    assert response.status_code == 200
    assert response.json()["audio_data_uri"].startswith("data:audio/mpeg;base64,")


@pytest.mark.unit
@pytest.mark.parametrize(
    "extra", [{"professor_id": OWNED_BY_OTHER}, {"professor_id": NO_OWNER}, {}]
)
def test_creator_cannot_preview_without_owning_the_professor(
    client: TestClient, voice_service, as_creator, tts_backend, extra
):
    assert _preview(client, **extra).status_code == 403
    tts_backend.text_to_speech.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("extra", [{"professor_id": NO_OWNER}, {}])
def test_admin_can_always_preview(client: TestClient, voice_service, tts_backend, extra):
    assert _preview(client, **extra).status_code == 200
