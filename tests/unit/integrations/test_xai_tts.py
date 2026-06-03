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
