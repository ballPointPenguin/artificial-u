"""
Primary/alternate API key failover for ElevenLabs.

ElevenLabs bills per account, and an exhausted account rejects generation requests with
HTTP 401 ``{"detail": {"status": "quota_exceeded", ...}}``. When a second (alternate) key is
configured, the key manager routes traffic to it from the moment the primary is exhausted
until the primary's own quota resets (``next_character_count_reset_unix`` from the
subscription endpoint), falling back to a fixed window if that timestamp is unavailable.

State is held in-process (the job worker runs inside the API process). After a restart the
manager starts on the primary again and simply re-detects exhaustion on the first failure.
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Optional, Tuple

AccountLabel = Literal["primary", "alt"]

# Used when the primary's reset time cannot be determined.
DEFAULT_FALLBACK_HOURS = 24
# Used when the reported reset time is already in the past (stale data): re-probe soon.
STALE_RESET_RECHECK = timedelta(hours=1)

logger = logging.getLogger(__name__)


def is_quota_error(exc: BaseException) -> bool:
    """Return True if ``exc`` is an ElevenLabs "quota exhausted" rejection.

    Works for both the SDK's ``ApiError`` (``.body``) and raw ``httpx.HTTPStatusError``
    (``.response``). Rate limiting (429 / concurrency) is intentionally not a quota error.
    """
    parts = [str(exc), str(getattr(exc, "body", "") or "")]
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            parts.append(response.text)
        except Exception:  # streaming responses that were never read
            pass
    return "quota_exceeded" in " ".join(parts).lower()


class ElevenLabsKeyManager:
    """Tracks which of the two ElevenLabs keys is currently in use."""

    def __init__(
        self,
        primary_key: str,
        alt_key: Optional[str] = None,
        fallback_hours: int = DEFAULT_FALLBACK_HOURS,
    ):
        self.primary_key = primary_key
        self.alt_key = alt_key or None
        self.fallback = timedelta(hours=fallback_hours)
        self._failover_until: Optional[datetime] = None
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return bool(self.alt_key) and self.alt_key != self.primary_key

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _expire_locked(self, now: datetime) -> None:
        if self._failover_until is not None and self._failover_until <= now:
            logger.info("ElevenLabs failover window elapsed; returning to primary key")
            self._failover_until = None

    def active_label(self) -> AccountLabel:
        if not self.enabled:
            return "primary"
        with self._lock:
            self._expire_locked(self._now())
            return "alt" if self._failover_until is not None else "primary"

    def active_key(self) -> str:
        if self.active_label() == "alt" and self.alt_key:
            return self.alt_key
        return self.primary_key

    @property
    def failover_until(self) -> Optional[datetime]:
        with self._lock:
            self._expire_locked(self._now())
            return self._failover_until

    def activate_alt(self, primary_resets_at: Optional[datetime] = None) -> datetime:
        """Route traffic to the alt key until the primary's quota is expected to reset.

        Args:
            primary_resets_at: The primary account's next quota reset, if known.

        Returns:
            The moment the manager will return to the primary key.
        """
        now = self._now()
        if primary_resets_at is None:
            until = now + self.fallback
        elif primary_resets_at <= now:
            until = now + STALE_RESET_RECHECK
        else:
            until = primary_resets_at
        with self._lock:
            self._failover_until = until
        logger.warning(
            "ElevenLabs primary key exhausted; using alt key until %s", until.isoformat()
        )
        return until

    def reset(self) -> None:
        """Return to the primary key immediately (manual override)."""
        with self._lock:
            self._failover_until = None

    def snapshot(self) -> Tuple[AccountLabel, Optional[datetime]]:
        return self.active_label(), self.failover_until


_managers: Dict[Tuple[str, Optional[str]], ElevenLabsKeyManager] = {}
_managers_lock = threading.Lock()


def get_key_manager(primary_key: str, alt_key: Optional[str]) -> ElevenLabsKeyManager:
    """Return the process-wide manager for this key pair (created on first use)."""
    cache_key = (primary_key, alt_key or None)
    with _managers_lock:
        manager = _managers.get(cache_key)
        if manager is None:
            manager = _managers[cache_key] = ElevenLabsKeyManager(primary_key, alt_key)
        return manager


def reset_key_managers() -> None:
    """Drop all cached managers (used by tests)."""
    with _managers_lock:
        _managers.clear()


def reset_time_from_subscription(status: Dict[str, Any]) -> Optional[datetime]:
    """Extract the next quota reset (UTC) from a ``get_subscription_status`` result."""
    reset_unix = status.get("next_reset_unix")
    if not reset_unix:
        return None
    return datetime.fromtimestamp(reset_unix, tz=timezone.utc)
