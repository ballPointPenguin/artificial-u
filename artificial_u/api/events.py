import asyncio
import json
from typing import Any, AsyncIterator, Dict, Iterable, Optional, Set


class JobEventHub:
    """
    In-process pub/sub hub for job state change events.

    Events are plain dicts; typical schema:
      { id, kind, status, payload, result? }
    """

    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: Dict[str, Any]) -> None:
        async with self._lock:
            for q in list(self._subscribers):
                if not q.full():
                    q.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[Dict[str, Any]]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                self._subscribers.discard(queue)


def _event_matches(
    event: Dict[str, Any],
    *,
    lecture_id: Optional[int],
    topic_id: Optional[int],
    kinds_set: Set[str],
) -> bool:
    if kinds_set and event.get("kind") not in kinds_set:
        return False
    payload = event.get("payload") or {}
    if lecture_id is not None and payload.get("lecture_id") != lecture_id:
        return False
    if topic_id is not None:
        tid = payload.get("topic_id") or (payload.get("partial_attributes") or {}).get("topic_id")
        if tid != topic_id:
            return False
    return True


async def sse_stream(
    hub: JobEventHub,
    *,
    lecture_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    kinds: Optional[Iterable[str]] = None,
    heartbeat_secs: int = 20,
) -> AsyncIterator[str]:
    """Yield Server-Sent Events strings filtered by optional params."""

    kinds_set: Set[str] = set(kinds or [])
    events = hub.subscribe()
    next_heartbeat = asyncio.get_event_loop().time() + heartbeat_secs

    try:
        while True:
            # Heartbeat
            now = asyncio.get_event_loop().time()
            if now >= next_heartbeat:
                yield "event: ping\ndata: {}\n\n"
                next_heartbeat = now + heartbeat_secs

            ev = await events.__anext__()
            if _event_matches(ev, lecture_id=lecture_id, topic_id=topic_id, kinds_set=kinds_set):
                data = json.dumps(ev, default=str)
                yield f"event: job\ndata: {data}\n\n"
    except asyncio.CancelledError:
        return
