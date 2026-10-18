"""
Admin endpoints for the ElevenLabs primary/alternate account failover.

Reports which account is serving text-to-speech and live usage / billing-cycle details for
each configured account. API keys are never returned.
"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from artificial_u.api.security.auth0 import require_role
from artificial_u.config import get_settings
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.failover import get_key_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/elevenlabs",
    tags=["admin"],
    dependencies=[require_role("admin")],
)


class ElevenLabsAccountStatus(BaseModel):
    """Usage snapshot for one ElevenLabs account."""

    label: Literal["primary", "alt"]
    configured: bool
    active: bool = Field(..., description="Whether this account is currently serving requests")
    tier: Optional[str] = None
    status: Optional[str] = None
    character_count: Optional[int] = None
    character_limit: Optional[int] = None
    characters_remaining: Optional[int] = None
    percent_used: Optional[float] = None
    next_reset_at: Optional[datetime] = Field(default=None, description="Next quota reset (UTC)")
    billing_period: Optional[str] = None
    error: Optional[str] = Field(default=None, description="Set when usage could not be fetched")


class ElevenLabsStatusResponse(BaseModel):
    """Failover state plus per-account usage."""

    failover_enabled: bool
    active_account: Literal["primary", "alt"]
    failover_until: Optional[datetime] = Field(
        default=None, description="When traffic returns to the primary (UTC); null while on primary"
    )
    accounts: List[ElevenLabsAccountStatus]


def _account_status(
    label: Literal["primary", "alt"], key: Optional[str], active: bool
) -> ElevenLabsAccountStatus:
    base = ElevenLabsAccountStatus(label=label, configured=bool(key), active=active)
    if not key:
        return base
    try:
        # Explicit key => this client never fails over; it reports on exactly this account.
        sub = ElevenLabsClient(api_key=key, alt_api_key="").get_subscription_status()
    except Exception as e:
        logger.warning("Could not fetch ElevenLabs %s subscription: %s", label, e)
        return base.model_copy(update={"error": str(e)[:200]})

    limit = sub["character_limit"]
    reset_unix = sub["next_reset_unix"]
    return base.model_copy(
        update={
            "tier": sub["tier"],
            "status": sub["status"],
            "character_count": sub["character_count"],
            "character_limit": limit,
            "characters_remaining": sub["characters_remaining"],
            "percent_used": round(100 * sub["character_count"] / limit, 1) if limit else None,
            "next_reset_at": (
                datetime.fromtimestamp(reset_unix, tz=timezone.utc) if reset_unix else None
            ),
            "billing_period": sub["billing_period"] or None,
        }
    )


def _build_status() -> ElevenLabsStatusResponse:
    settings = get_settings()
    primary, alt = settings.ELEVENLABS_API_KEY, settings.ELEVENLABS_API_KEY_ALT
    if primary:
        manager = get_key_manager(primary, alt)
        active, until = manager.snapshot()
        enabled = manager.enabled
    else:
        active, until, enabled = "primary", None, False
    return ElevenLabsStatusResponse(
        failover_enabled=enabled,
        active_account=active,
        failover_until=until,
        accounts=[
            _account_status("primary", primary, active == "primary"),
            _account_status("alt", alt, active == "alt"),
        ],
    )


@router.get(
    "/status",
    response_model=ElevenLabsStatusResponse,
    summary="ElevenLabs account status",
    description="Active account, failover window, and live usage for each configured account.",
)
def get_elevenlabs_status() -> ElevenLabsStatusResponse:
    return _build_status()


@router.post(
    "/reset",
    response_model=ElevenLabsStatusResponse,
    summary="Return to the primary ElevenLabs account",
    description="Clears the failover window. If the primary is still exhausted it will "
    "fail over again on the next request.",
)
def reset_elevenlabs_failover() -> ElevenLabsStatusResponse:
    settings = get_settings()
    if settings.ELEVENLABS_API_KEY:
        get_key_manager(settings.ELEVENLABS_API_KEY, settings.ELEVENLABS_API_KEY_ALT).reset()
    return _build_status()
