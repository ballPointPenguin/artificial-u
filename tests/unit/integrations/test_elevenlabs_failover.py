"""Tests for ElevenLabs primary/alt key failover."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from elevenlabs.core.api_error import ApiError

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.failover import (
    ElevenLabsKeyManager,
    get_key_manager,
    is_quota_error,
    reset_key_managers,
)

pytestmark = pytest.mark.unit

QUOTA_BODY = {"detail": {"status": "quota_exceeded", "message": "You have 0 credits remaining"}}


def quota_error() -> ApiError:
    return ApiError(status_code=401, body=QUOTA_BODY)


@pytest.fixture(autouse=True)
def _fresh_managers():
    reset_key_managers()
    yield
    reset_key_managers()


def now():
    return datetime.now(timezone.utc)


class TestIsQuotaError:
    def test_sdk_api_error(self):
        assert is_quota_error(quota_error())

    def test_httpx_status_error(self):
        request = httpx.Request("POST", "https://api.elevenlabs.io/v1/x")
        response = httpx.Response(401, json=QUOTA_BODY, request=request)
        assert is_quota_error(httpx.HTTPStatusError("401", request=request, response=response))

    def test_rate_limit_is_not_quota(self):
        body = {"detail": {"status": "too_many_concurrent_requests"}}
        assert not is_quota_error(ApiError(status_code=429, body=body))

    def test_unrelated_error(self):
        assert not is_quota_error(RuntimeError("boom"))


class TestKeyManager:
    def test_disabled_without_alt(self):
        mgr = ElevenLabsKeyManager("p")
        assert not mgr.enabled
        assert mgr.active_key() == "p"

    def test_disabled_when_alt_equals_primary(self):
        assert not ElevenLabsKeyManager("p", "p").enabled

    def test_uses_primary_reset_time(self):
        mgr = ElevenLabsKeyManager("p", "a")
        reset = now() + timedelta(days=9)
        assert mgr.activate_alt(reset) == reset
        assert mgr.active_label() == "alt"
        assert mgr.active_key() == "a"

    def test_unknown_reset_falls_back_to_24h(self):
        mgr = ElevenLabsKeyManager("p", "a")
        until = mgr.activate_alt(None)
        assert timedelta(hours=23, minutes=59) < until - now() <= timedelta(hours=24)

    def test_stale_reset_rechecks_soon(self):
        mgr = ElevenLabsKeyManager("p", "a")
        until = mgr.activate_alt(now() - timedelta(days=1))
        assert until - now() <= timedelta(hours=1)

    def test_returns_to_primary_after_window(self):
        mgr = ElevenLabsKeyManager("p", "a")
        mgr.activate_alt(now() + timedelta(seconds=30))
        mgr._failover_until = now() - timedelta(seconds=1)
        assert mgr.active_label() == "primary"
        assert mgr.failover_until is None

    def test_manual_reset(self):
        mgr = ElevenLabsKeyManager("p", "a")
        mgr.activate_alt(None)
        mgr.reset()
        assert mgr.active_key() == "p"

    def test_cache_shares_state_per_key_pair(self):
        assert get_key_manager("p", "a") is get_key_manager("p", "a")
        assert get_key_manager("p", "a") is not get_key_manager("p", "b")


def make_client(primary="primary-key", alt="alt-key"):
    """Client whose SDK objects are mocks, one per key, recorded in ``sdks``."""
    sdks = {}

    client = ElevenLabsClient(api_key=primary, alt_api_key=alt)

    def init_sdk(key):
        sdks.setdefault(key, MagicMock(name=key))
        client.api_key = key
        client.client = sdks[key]
        client.headers = {"xi-api-key": key}

    client._init_sdk = init_sdk
    init_sdk(client._failover.active_key() if client._failover else primary)
    return client, sdks


def subscription(reset_unix=None, count=10_000, limit=10_000):
    return SimpleNamespace(
        tier="creator",
        status="active",
        character_count=count,
        character_limit=limit,
        next_character_count_reset_unix=reset_unix,
        billing_period="monthly_period",
        character_refresh_period="monthly_period",
    )


class TestClientFailover:
    def test_no_failover_without_alt_raises_immediately(self):
        client = ElevenLabsClient(api_key="only-key")
        client.client = MagicMock()
        client.client.text_to_speech.convert.side_effect = quota_error()
        with pytest.raises(ApiError):
            client.text_to_speech("hi", "voice")
        # quota errors are not retried
        assert client.client.text_to_speech.convert.call_count == 1

    def test_switches_to_alt_until_primary_reset(self):
        client, sdks = make_client()
        reset = now() + timedelta(days=5)
        sdks["primary-key"].text_to_speech.convert.side_effect = quota_error()
        sdks["primary-key"].user.subscription.get.return_value = subscription(
            reset_unix=int(reset.timestamp())
        )
        sdks.setdefault("alt-key", MagicMock()).text_to_speech.convert.return_value = [b"audio"]

        assert client.text_to_speech("hi", "voice") == b"audio"

        mgr = get_key_manager("primary-key", "alt-key")
        assert mgr.active_label() == "alt"
        assert abs((mgr.failover_until - reset).total_seconds()) < 1
        assert client.api_key == "alt-key"

    def test_other_client_instances_adopt_active_key(self):
        client, sdks = make_client()
        get_key_manager("primary-key", "alt-key").activate_alt(None)
        sdks.setdefault("alt-key", MagicMock()).text_to_speech.convert.return_value = [b"x"]

        assert client.text_to_speech("hi", "voice") == b"x"
        sdks["primary-key"].text_to_speech.convert.assert_not_called()

    def test_both_accounts_exhausted_raises(self):
        client, sdks = make_client()
        sdks["primary-key"].user.subscription.get.return_value = subscription()
        sdks["primary-key"].text_to_speech.convert.side_effect = quota_error()
        sdks.setdefault("alt-key", MagicMock()).text_to_speech.convert.side_effect = quota_error()

        with pytest.raises(ApiError):
            client.text_to_speech("hi", "voice")
        assert sdks["alt-key"].text_to_speech.convert.call_count == 1

    def test_unknown_reset_time_still_fails_over(self):
        client, sdks = make_client()
        sdks["primary-key"].text_to_speech.convert.side_effect = quota_error()
        sdks["primary-key"].user.subscription.get.side_effect = RuntimeError("down")
        sdks.setdefault("alt-key", MagicMock()).text_to_speech.convert.return_value = [b"ok"]

        assert client.text_to_speech("hi", "voice") == b"ok"
        assert get_key_manager("primary-key", "alt-key").failover_until is not None

    def test_non_quota_errors_do_not_fail_over(self):
        client, sdks = make_client()
        sdks["primary-key"].text_to_speech.convert.side_effect = RuntimeError("500")
        client.RETRY_WAIT = 0

        with pytest.raises(RuntimeError):
            client.text_to_speech("hi", "voice")
        assert get_key_manager("primary-key", "alt-key").active_label() == "primary"


def test_subscription_status_summary():
    client = ElevenLabsClient(api_key="k", alt_api_key="")
    client.client = MagicMock()
    client.client.user.subscription.get.return_value = subscription(
        reset_unix=1_900_000_000, count=2_500, limit=10_000
    )

    status = client.get_subscription_status()

    assert status["characters_remaining"] == 7_500
    assert status["next_reset_unix"] == 1_900_000_000
    assert status["tier"] == "creator"


def test_voice_missing_on_alt_account_gets_explanatory_error():
    client, sdks = make_client()
    sdks["primary-key"].text_to_speech.convert.side_effect = quota_error()
    sdks["primary-key"].user.subscription.get.return_value = subscription()
    missing = ApiError(status_code=404, body={"detail": {"status": "voice_not_found"}})
    sdks.setdefault("alt-key", MagicMock()).text_to_speech.convert.side_effect = missing

    with pytest.raises(RuntimeError, match="custom voices are not shared"):
        client.text_to_speech("hi", "voice")
