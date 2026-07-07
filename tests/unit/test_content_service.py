"""Unit tests for ContentService, focused on Claude model version gating.

These tests cover version/tier parsing and the feature flags derived from it
(prefill support, sampling params, effort, and adaptive-thinking defaults),
including the naming style introduced with Claude Sonnet 5 (e.g.
``claude-sonnet-5``, with no explicit minor version).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.services.content_service import ContentService


def _build_service():
    settings = SimpleNamespace(content_backend="anthropic", content_model="claude-sonnet-4-6")
    service = ContentService.__new__(ContentService)
    service.logger = MagicMock()
    service.default_backend = settings.content_backend
    service.default_model = settings.content_model
    service.storage_service = MagicMock()
    service.storage_service.upload_content_log = AsyncMock(return_value=(True, "http://log"))
    return service


@pytest.mark.parametrize(
    "model,expected",
    [
        ("claude-sonnet-4-6", (4, 6)),
        ("claude-opus-4-8", (4, 8)),
        ("claude-haiku-4-5", (4, 5)),
        ("claude-sonnet-5", (5, 0)),
        ("claude-opus-5", (5, 0)),
        ("claude-sonnet-5-1", (5, 1)),
        ("claude-sonnet-5-20260601", (5, 0)),
        ("claude-3-7-sonnet-latest", None),
        ("claude-3-5-sonnet-20241022", None),
        ("claude-3-opus-20240229", None),
        ("gpt-5.5", None),
    ],
)
def test_parse_claude_version(model, expected):
    assert ContentService._parse_claude_version(model) == expected


@pytest.mark.parametrize(
    "model,expected",
    [
        ("claude-sonnet-4-6", "sonnet"),
        ("claude-opus-4-8", "opus"),
        ("claude-sonnet-5", "sonnet"),
        ("claude-opus-5", "opus"),
        ("claude-3-7-sonnet-latest", None),
        ("gpt-5.5", None),
    ],
)
def test_parse_claude_tier(model, expected):
    assert ContentService._parse_claude_tier(model) == expected


class TestVersionGatedFeatures:
    def setup_method(self):
        self.service = _build_service()

    @pytest.mark.parametrize(
        "model,expected",
        [
            ("claude-3-7-sonnet-latest", True),  # old-style, unrecognized -> assume supported
            ("claude-sonnet-4-6", False),  # 4.6+ rejects prefill
            ("claude-opus-4-8", False),
            ("claude-sonnet-5", False),  # Sonnet 5 also rejects prefill
        ],
    )
    def test_is_prefill_supported(self, model, expected):
        assert self.service._is_prefill_supported(model) is expected

    @pytest.mark.parametrize(
        "model,expected",
        [
            ("claude-sonnet-4-6", True),  # < 4.7, still accepts sampling params
            ("claude-opus-4-8", False),  # 4.7+ rejects sampling params
            ("claude-sonnet-5", False),  # Sonnet 5 also rejects sampling params
        ],
    )
    def test_supports_sampling_params(self, model, expected):
        assert self.service._supports_sampling_params(model) is expected

    @pytest.mark.parametrize(
        "model,expected",
        [
            ("claude-3-7-sonnet-latest", False),  # old-style, no effort support
            ("claude-sonnet-4-6", True),
            ("claude-opus-4-8", True),
            ("claude-sonnet-5", True),
        ],
    )
    def test_supports_effort(self, model, expected):
        assert self.service._supports_effort(model) is expected

    @pytest.mark.parametrize(
        "model,expected",
        [
            ("claude-sonnet-4-6", False),  # thinking off by default
            ("claude-opus-4-8", False),  # thinking off by default (adaptive requires opt-in)
            ("claude-sonnet-5", True),  # adaptive thinking on by default
            ("claude-sonnet-5-1", True),
            ("claude-opus-5", False),  # not a sonnet-tier model
        ],
    )
    def test_defaults_to_adaptive_thinking(self, model, expected):
        assert self.service._defaults_to_adaptive_thinking(model) is expected


@pytest.mark.asyncio
async def test_generate_anthropic_disables_thinking_for_sonnet_5(monkeypatch):
    service = _build_service()

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [SimpleNamespace(type="text", text="hello world")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr("artificial_u.services.content_service.anthropic_client", mock_client)

    await service._generate_anthropic(
        "prompt", "claude-sonnet-5", "system", None, None, None, effort=None
    )

    call_kwargs = mock_client.messages.create.await_args.kwargs
    assert call_kwargs["thinking"] == {"type": "disabled"}
    assert "temperature" not in call_kwargs
    assert call_kwargs["output_config"] == {"effort": "medium"}


@pytest.mark.asyncio
async def test_generate_anthropic_leaves_thinking_unset_for_opus_4_8(monkeypatch):
    service = _build_service()

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [SimpleNamespace(type="text", text="hello world")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr("artificial_u.services.content_service.anthropic_client", mock_client)

    await service._generate_anthropic(
        "prompt", "claude-opus-4-8", "system", None, None, None, effort=None
    )

    call_kwargs = mock_client.messages.create.await_args.kwargs
    assert "thinking" not in call_kwargs
    assert "temperature" not in call_kwargs


@pytest.mark.asyncio
async def test_generate_anthropic_uses_sampling_params_for_sonnet_4_6(monkeypatch):
    service = _build_service()

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [SimpleNamespace(type="text", text="hello world")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr("artificial_u.services.content_service.anthropic_client", mock_client)

    await service._generate_anthropic(
        "prompt", "claude-sonnet-4-6", "system", None, None, None, effort=None
    )

    call_kwargs = mock_client.messages.create.await_args.kwargs
    assert "thinking" not in call_kwargs
    assert call_kwargs["temperature"] == pytest.approx(0.3)
