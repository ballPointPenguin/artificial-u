"""Unit tests for the Qwen (Alibaba) TTS client, backend adapter, and factory."""

import pytest

from artificial_u.integrations.qwen.tts_client import QwenTTSClient
from artificial_u.integrations.qwen.voice_manager import (
    FLASH_MODEL,
    PLUS_MODEL,
    QWEN_VOICES,
    QwenVoiceManager,
    model_for_voice,
)
from artificial_u.integrations.tts.factory import create_tts_backend
from artificial_u.integrations.tts.qwen_backend import QwenTTSBackend


class _FakeSynthesizer:
    """Stand-in for dashscope SpeechSynthesizer capturing constructor args."""

    last_call = {}
    audio = b"audio-bytes"

    def __init__(self, model=None, voice=None, format=None, url=None, **kwargs):
        _FakeSynthesizer.last_call = {
            "model": model,
            "voice": voice,
            "format": format,
            "url": url,
        }

    def call(self, text, timeout_millis=None):
        _FakeSynthesizer.last_call["text"] = text
        return _FakeSynthesizer.audio


@pytest.fixture
def patch_synthesizer(monkeypatch):
    import dashscope.audio.tts_v2 as tts_v2

    _FakeSynthesizer.last_call = {}
    _FakeSynthesizer.audio = b"audio-bytes"
    monkeypatch.setattr(tts_v2, "SpeechSynthesizer", _FakeSynthesizer)
    return _FakeSynthesizer


@pytest.mark.unit
def test_client_calls_synthesizer_with_voice_and_url(patch_synthesizer):
    client = QwenTTSClient(api_key="key-123", wss_url="wss://example.test/api-ws/v1/inference")
    audio = client.text_to_speech("Hello world", voice_id="loongjohn")

    assert audio == b"audio-bytes"
    call = patch_synthesizer.last_call
    assert call["voice"] == "loongjohn"
    assert call["model"] == FLASH_MODEL
    assert call["url"] == "wss://example.test/api-ws/v1/inference"
    assert call["text"] == "Hello world"
    assert "MP3" in str(call["format"])

    import dashscope

    assert dashscope.api_key == "key-123"


@pytest.mark.unit
def test_client_defaults_voice(patch_synthesizer):
    client = QwenTTSClient(api_key="key")
    client.text_to_speech("Hi there everyone")
    assert patch_synthesizer.last_call["voice"] == QwenTTSClient.DEFAULT_VOICE


@pytest.mark.unit
def test_client_resolves_plus_model_from_voice(patch_synthesizer):
    client = QwenTTSClient(api_key="key")
    client.text_to_speech("text", voice_id="longanlingxin")
    assert patch_synthesizer.last_call["model"] == PLUS_MODEL


@pytest.mark.unit
def test_client_explicit_model_overrides_voice_mapping(patch_synthesizer):
    client = QwenTTSClient(api_key="key")
    client.text_to_speech("text", voice_id="longanlingxin", model="custom-model")
    assert patch_synthesizer.last_call["model"] == "custom-model"


@pytest.mark.unit
def test_client_unknown_voice_falls_back_to_settings_model(patch_synthesizer):
    client = QwenTTSClient(api_key="key")
    client.text_to_speech("text", voice_id="some-cloned-voice-id")
    assert patch_synthesizer.last_call["model"] == client.default_model


@pytest.mark.unit
def test_client_retries_then_raises(monkeypatch):
    import dashscope.audio.tts_v2 as tts_v2

    monkeypatch.setattr("artificial_u.integrations.qwen.tts_client.time.sleep", lambda *_: None)

    attempts = {"n": 0}

    class _AlwaysFails(_FakeSynthesizer):
        def call(self, text, timeout_millis=None):
            attempts["n"] += 1
            raise ConnectionError("boom")

    monkeypatch.setattr(tts_v2, "SpeechSynthesizer", _AlwaysFails)
    client = QwenTTSClient(api_key="key")
    with pytest.raises(ConnectionError):
        client.text_to_speech("text")
    assert attempts["n"] == QwenTTSClient.MAX_RETRIES


@pytest.mark.unit
def test_client_raises_on_empty_audio(monkeypatch, patch_synthesizer):
    monkeypatch.setattr("artificial_u.integrations.qwen.tts_client.time.sleep", lambda *_: None)
    patch_synthesizer.audio = None
    client = QwenTTSClient(api_key="key")
    with pytest.raises(RuntimeError):
        client.text_to_speech("text")


@pytest.mark.unit
def test_backend_adapter_uses_client(patch_synthesizer):
    client = QwenTTSClient(api_key="key")
    backend = QwenTTSBackend(client=client)
    assert backend.backend_name == "qwen"

    backend.text_to_speech("Some lecture text here", voice_id="loongmary")
    assert patch_synthesizer.last_call["voice"] == "loongmary"


@pytest.mark.unit
def test_backend_ignores_unrelated_kwargs(patch_synthesizer):
    """language / voice_settings (used by other backends) must not break Qwen."""
    client = QwenTTSClient(api_key="key")
    backend = QwenTTSBackend(client=client)
    backend.text_to_speech(
        "text here please", voice_id="loongjohn", language="en", voice_settings={"x": 1}
    )
    assert patch_synthesizer.last_call["voice"] == "loongjohn"


@pytest.mark.unit
def test_factory_creates_qwen_backend(patch_synthesizer):
    backend = create_tts_backend(backend_name="qwen", api_key="key")
    assert isinstance(backend, QwenTTSBackend)
    assert backend.backend_name == "qwen"


# ---------------------------------------------------------------------------
# Voice manager (static preset catalog)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_voice_manager_lists_all_voices():
    voices = QwenVoiceManager().list_voices()
    assert len(voices) == len(QWEN_VOICES)
    ids = {v["id"] for v in voices}
    assert {"loongeva_v3.6", "loongjohn", "longanlingxin", "longanlufeng"} <= ids
    # No child voices are exposed
    assert "longjielidou_v3.6" not in ids
    # Every voice has a valid model and at least one language
    for v in voices:
        assert v["model"] in (FLASH_MODEL, PLUS_MODEL)
        assert v["languages"]


@pytest.mark.unit
def test_voice_manager_includes_chinese_only_base_voices():
    """Base (cloned) voices are Mandarin-only and use model-prefixed ids."""
    mgr = QwenVoiceManager()
    kai = mgr.get_voice("qwen-audio-3.0-tts-plus-longyinghaikai")
    assert kai is not None
    assert kai["languages"] == ["zh"]
    assert kai["gender"] == "female"
    assert kai["model"] == PLUS_MODEL


@pytest.mark.unit
def test_voice_manager_get_voice():
    mgr = QwenVoiceManager()
    john = mgr.get_voice("loongjohn")
    assert john["gender"] == "male"
    assert john["model"] == FLASH_MODEL
    lufeng = mgr.get_voice("longanlufeng")
    assert lufeng["gender"] == "male"
    assert mgr.get_voice("nonexistent") is None


@pytest.mark.unit
def test_model_for_voice():
    assert model_for_voice("longanlufeng") == PLUS_MODEL
    assert model_for_voice("loongeva_v3.6") == FLASH_MODEL
    assert model_for_voice("qwen-audio-3.0-tts-plus-longyinghaikai") == PLUS_MODEL
    assert model_for_voice("nonexistent") is None
