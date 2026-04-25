from __future__ import annotations

import httpx

_shared_async_client: httpx.AsyncClient | None = None


def get_shared_async_client() -> httpx.AsyncClient:
    """Return the process-level async HTTP client used for outbound fetches."""
    global _shared_async_client
    if _shared_async_client is None or _shared_async_client.is_closed:
        _shared_async_client = httpx.AsyncClient()
    return _shared_async_client


async def close_shared_async_client() -> None:
    """Close the process-level async HTTP client during application shutdown."""
    global _shared_async_client
    if _shared_async_client is not None and not _shared_async_client.is_closed:
        await _shared_async_client.aclose()
    _shared_async_client = None
