"""Unit tests for the Qwen (Alibaba) TTS client, backend adapter, and factory."""

import importlib.util
from pathlib import Path

import httpx
import pytest

from artificial_u.config.defaults import DEFAULT_QWEN_TTS_MODEL
from artificial_u.integrations.qwen.tts_client import QwenTTSClient
from artificial_u.integrations.qwen.voice_manager import QWEN_VOICES, QwenVoiceManager
from artificial_u.integrations.tts.factory import create_tts_backend
from artificial_u.integrations.tts.qwen_backend import QwenTTSBackend

AUDIO_URL = "https://oss.example.test/audio.mp3"
API_PATH = "/api/v1/services/audio/tts/SpeechSynthesizer"


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr("artificial_u.integrations.qwen.tts_client.time.sleep", lambda *_: None)


@pytest.fixture
def mock_api(monkeypatch):
    """Route httpx.Client through a MockTransport; records requests."""
    state = {"requests": [], "api_status": 200, "api_json": None, "audio": b"audio-bytes"}

    def handler(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        if request.url.path == API_PATH:
            body = state["api_json"]
            if body is None:
                body = {"output": {"audio": {"url": AUDIO_URL}}}
            return httpx.Response(state["api_status"], json=body)
        return httpx.Response(200, content=state["audio"])

    real_client = httpx.Client
    monkeypatch.setattr(
        "artificial_u.integrations.qwen.tts_client.httpx.Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )
    return state


def _client(**kwargs):
    return QwenTTSClient(api_key="key-123", workspace_id="ws1", **kwargs)


@pytest.mark.unit
def test_client_posts_documented_request(mock_api):
    audio = _client().text_to_speech("Hello world", voice_id="Emily_v3.1")

    assert audio == b"audio-bytes"
    api_req, audio_req = mock_api["requests"]
    assert str(api_req.url) == f"https://ws1.ap-southeast-1.maas.aliyuncs.com{API_PATH}"
    assert api_req.headers["Authorization"] == "Bearer key-123"
    import json

    body = json.loads(api_req.content)
    assert body["model"] == DEFAULT_QWEN_TTS_MODEL == "qwen-audio-3.1-tts-flash"
    assert body["input"]["text"] == "Hello world"
    assert body["input"]["voice"] == "Emily_v3.1"
    assert body["input"]["format"] == "mp3"
    assert str(audio_req.url) == AUDIO_URL


@pytest.mark.unit
def test_client_region_and_model_override(mock_api):
    _client(region="cn-beijing").text_to_speech("text", model="custom-model")
    import json

    api_req = mock_api["requests"][0]
    assert api_req.url.host == "ws1.cn-beijing.maas.aliyuncs.com"
    assert json.loads(api_req.content)["model"] == "custom-model"


@pytest.mark.unit
def test_client_defaults_voice(mock_api):
    import json

    _client().text_to_speech("text")
    body = json.loads(mock_api["requests"][0].content)
    assert body["input"]["voice"] == QwenTTSClient.DEFAULT_VOICE == "Brian_v3.1"


@pytest.mark.unit
def test_client_retries_throttling_then_raises(mock_api, no_sleep):
    mock_api["api_status"] = 429
    mock_api["api_json"] = {"code": "Throttling.RateQuota", "message": "slow down"}
    with pytest.raises(httpx.HTTPStatusError, match="Throttling.RateQuota"):
        _client().text_to_speech("text")
    assert len(mock_api["requests"]) == QwenTTSClient.MAX_RETRIES


@pytest.mark.unit
def test_client_does_not_retry_auth_errors(mock_api, no_sleep):
    mock_api["api_status"] = 401
    mock_api["api_json"] = {"code": "InvalidApiKey", "message": "bad key"}
    with pytest.raises(httpx.HTTPStatusError, match="InvalidApiKey"):
        _client().text_to_speech("text")
    assert len(mock_api["requests"]) == 1


@pytest.mark.unit
def test_client_raises_when_response_has_no_audio_url(mock_api, no_sleep):
    mock_api["api_json"] = {"output": {"audio": {"url": ""}}}
    with pytest.raises(RuntimeError, match="no audio URL"):
        _client().text_to_speech("text")


@pytest.mark.unit
def test_client_raises_on_empty_audio(mock_api, no_sleep):
    mock_api["audio"] = b""
    with pytest.raises(RuntimeError, match="no audio data"):
        _client().text_to_speech("text")


@pytest.mark.unit
def test_backend_adapter_uses_client(mock_api):
    backend = QwenTTSBackend(client=_client())
    assert backend.backend_name == "qwen"
    assert backend.text_to_speech("Some lecture text here", voice_id="Eric_v3.1") == b"audio-bytes"


@pytest.mark.unit
def test_backend_ignores_unrelated_kwargs(mock_api):
    """language / voice_settings (used by other backends) must not break Qwen."""
    backend = QwenTTSBackend(client=_client())
    backend.text_to_speech(
        "text here please", voice_id="Brian_v3.1", language="en", voice_settings={"x": 1}
    )
    assert len(mock_api["requests"]) == 2


@pytest.mark.unit
def test_factory_creates_qwen_backend():
    backend = create_tts_backend(backend_name="qwen", api_key="key")
    assert isinstance(backend, QwenTTSBackend)
    assert backend.backend_name == "qwen"


@pytest.mark.unit
def test_voice_manager_catalog():
    mgr = QwenVoiceManager()
    voices = mgr.list_voices()
    assert len(voices) == len(QWEN_VOICES)
    ids = [v["id"] for v in voices]
    assert len(ids) == len(set(ids))
    assert all(i.endswith("_v3.1") for i in ids)
    assert QwenTTSClient.DEFAULT_VOICE in ids
    # No child voices are exposed
    assert "longjielidou_v3.1" not in ids
    for v in voices:
        assert v["model"] == DEFAULT_QWEN_TTS_MODEL
        assert v["languages"]
    emily = mgr.get_voice("Emily_v3.1")
    assert (emily["gender"], emily["accent"], emily["languages"]) == ("female", "British", ["en"])
    assert mgr.get_voice("loongjohn") is None


def _load_backfill_script():
    path = Path(__file__).resolve().parents[3] / "scripts" / "backfill_qwen_voices_v31.py"
    spec = importlib.util.spec_from_file_location("backfill_qwen_voices_v31", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_backfill_script_mapping_targets_exist_in_catalog():
    script = _load_backfill_script()
    catalog = {v["id"] for v in QWEN_VOICES}
    assert set(script.VOICE_MAP.values()) <= catalog
    assert {script.FALLBACK_FEMALE, script.FALLBACK_MALE} <= catalog


@pytest.mark.unit
@pytest.mark.parametrize(
    "old_id,gender,expected",
    [
        ("loongjohn", "male", "Brian_v3.1"),
        ("loongmary", None, "Emily_v3.1"),
        ("longanhuan_v3.6", "female", "longanhuan_v3.1"),
        ("qwen-audio-3.0-tts-plus-longyinghaikai", "female", "Ava_v3.1"),
        ("qwen-audio-3.0-tts-plus-longyinghaixuan", "male", "Brian_v3.1"),
        ("unknown-voice", None, "Brian_v3.1"),
    ],
)
def test_backfill_script_replacement_voice_id(old_id, gender, expected):
    assert _load_backfill_script().replacement_voice_id(old_id, gender) == expected
