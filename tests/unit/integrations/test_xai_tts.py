"""Unit tests for the xAI (Grok) TTS client, backend adapter, and factory."""

import httpx
import pytest

from artificial_u.integrations.tts.factory import create_tts_backend
from artificial_u.integrations.tts.xai_backend import XAITTSBackend
from artificial_u.integrations.xai.tts_client import XAITTSClient


class _FakeResponse:
    def __init__(self, content=b"audio-bytes", status_code=200):
        self.content = content
        self.status_code = status_code
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)


class _FakeClient:
    """Stand-in for httpx.Client capturing the last POST call."""

    last_call = {}

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, json=None, headers=None):
        _FakeClient.last_call = {"url": url, "json": json, "headers": headers}
        return _FakeResponse()


@pytest.fixture
def patch_httpx(monkeypatch):
    _FakeClient.last_call = {}
    monkeypatch.setattr("artificial_u.integrations.xai.tts_client.httpx.Client", _FakeClient)
    return _FakeClient


@pytest.mark.unit
def test_client_posts_to_tts_endpoint_with_bearer(patch_httpx):
    client = XAITTSClient(api_key="key-123", base_url="https://api.x.ai/v1")
    audio = client.text_to_speech("Hello world", voice_id="ara", language="en")

    assert audio == b"audio-bytes"  # raw bytes, not JSON
    call = patch_httpx.last_call
    assert call["url"] == "https://api.x.ai/v1/tts"
    assert call["headers"]["Authorization"] == "Bearer key-123"
    body = call["json"]
    assert body["text"] == "Hello world"
    assert body["voice_id"] == "ara"
    assert body["language"] == "en"
    assert body["output_format"]["codec"] == "mp3"


@pytest.mark.unit
def test_client_defaults_voice_and_language(patch_httpx):
    client = XAITTSClient(api_key="key", base_url="https://api.x.ai/v1")
    client.text_to_speech("Hi there everyone")
    body = patch_httpx.last_call["json"]
    assert body["voice_id"] == "eve"
    assert body["language"] == "en"


@pytest.mark.unit
def test_client_retries_then_raises(monkeypatch):
    monkeypatch.setattr("artificial_u.integrations.xai.tts_client.time.sleep", lambda *_: None)

    attempts = {"n": 0}

    class _AlwaysFails(_FakeClient):
        def post(self, url, json=None, headers=None):
            attempts["n"] += 1
            raise httpx.ConnectError("boom")

    monkeypatch.setattr("artificial_u.integrations.xai.tts_client.httpx.Client", _AlwaysFails)
    client = XAITTSClient(api_key="key")
    with pytest.raises(httpx.ConnectError):
        client.text_to_speech("text")
    assert attempts["n"] == XAITTSClient.MAX_RETRIES


@pytest.mark.unit
def test_backend_adapter_uses_client(patch_httpx):
    client = XAITTSClient(api_key="key", base_url="https://api.x.ai/v1")
    backend = XAITTSBackend(client=client)
    assert backend.backend_name == "xai"

    backend.text_to_speech("Some lecture text here", voice_id="leo")
    body = patch_httpx.last_call["json"]
    assert body["voice_id"] == "leo"


@pytest.mark.unit
def test_backend_ignores_unrelated_kwargs(patch_httpx):
    """model_id / voice_settings (used by other backends) must not break xAI."""
    client = XAITTSClient(api_key="key", base_url="https://api.x.ai/v1")
    backend = XAITTSBackend(client=client)
    backend.text_to_speech(
        "text here please", voice_id="rex", model_id="ignored", voice_settings={"x": 1}
    )
    body = patch_httpx.last_call["json"]
    assert body["voice_id"] == "rex"


@pytest.mark.unit
def test_factory_creates_xai_backend(patch_httpx):
    backend = create_tts_backend(backend_name="xai", api_key="key")
    assert isinstance(backend, XAITTSBackend)
    assert backend.backend_name == "xai"


@pytest.mark.unit
def test_factory_rejects_unknown_backend():
    with pytest.raises(ValueError):
        create_tts_backend(backend_name="not-a-backend", api_key="key")


# ---------------------------------------------------------------------------
# Voice manager (live catalog from GET /tts/voices)
# ---------------------------------------------------------------------------


class _FakeVoicesResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeVoicesClient:
    """Stand-in for httpx.Client that returns a canned voices payload."""

    payload = {
        "voices": [
            {"voice_id": "eve", "name": "Eve", "language": "multilingual"},
            {"voice_id": "ara", "name": "Ara", "language": "multilingual"},
            {"voice_id": "camille", "name": "Camille", "language": "fr", "gender": "female"},
            {"voice_id": "xia", "name": "Xia", "language": "zh", "gender": "female"},
        ]
    }
    last_call = {}

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, headers=None):
        _FakeVoicesClient.last_call = {"url": url, "headers": headers}
        return _FakeVoicesResponse(self.payload)


@pytest.fixture
def patch_voices_httpx(monkeypatch):
    _FakeVoicesClient.last_call = {}
    monkeypatch.setattr(
        "artificial_u.integrations.xai.voice_manager.httpx.Client", _FakeVoicesClient
    )
    return _FakeVoicesClient


@pytest.mark.unit
def test_voice_manager_lists_all_voices(patch_voices_httpx):
    from artificial_u.integrations.xai.voice_manager import XAIVoiceManager

    mgr = XAIVoiceManager(api_key="key", base_url="https://api.x.ai/v1")
    voices = mgr.list_voices()

    assert patch_voices_httpx.last_call["url"] == "https://api.x.ai/v1/tts/voices"
    assert patch_voices_httpx.last_call["headers"]["Authorization"] == "Bearer key"
    # voice_id is normalized to id; language-specific voices included
    ids = {v["id"] for v in voices}
    assert ids == {"eve", "ara", "camille", "xia"}
    camille = next(v for v in voices if v["id"] == "camille")
    assert camille["name"] == "Camille"
    assert camille["language"] == "fr"
    assert camille["gender"] == "female"


@pytest.mark.unit
def test_voice_manager_get_voice(patch_voices_httpx):
    from artificial_u.integrations.xai.voice_manager import XAIVoiceManager

    mgr = XAIVoiceManager(api_key="key", base_url="https://api.x.ai/v1")
    assert mgr.get_voice("xia")["language"] == "zh"
    assert mgr.get_voice("nonexistent") is None
