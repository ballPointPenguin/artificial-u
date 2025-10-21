import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, Iterable, Optional, Set

from starlette.requests import Request

from artificial_u.api.config import get_settings

_STREAM_CLOSED = object()


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
        """Subscribe to job events. Yields events as they are published."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)

        async with self._lock:
            self._subscribers.add(queue)

        try:
            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.getLogger(__name__).error(f"Subscribe error: {e}", exc_info=True)
            raise
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


async def _event_reader(events: AsyncIterator[Dict[str, Any]], event_queue: asyncio.Queue) -> None:
    """Read events from the hub and put them in a local queue."""
    logger = logging.getLogger(__name__)
    try:
        async for event in events:
            await event_queue.put(event)
    except Exception as e:
        logger.error(f"Event reader error: {e}")
        await event_queue.put(_STREAM_CLOSED)


async def sse_stream(
    hub: JobEventHub,
    *,
    request: Optional[Request] = None,
    lecture_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    kinds: Optional[Iterable[str]] = None,
    heartbeat_secs: int = 5,
) -> AsyncIterator[str]:
    """Yield Server-Sent Events strings filtered by optional params.

    Designed to be resilient to disconnects and cooperative with shutdown/reload.
    """
    logger = logging.getLogger(__name__)
    kinds_set: Set[str] = set(kinds or [])

    events = hub.subscribe()
    loop = asyncio.get_event_loop()
    settings = get_settings()
    keepalive_interval = float(getattr(settings, "SSE_KEEPALIVE_INTERVAL_SEC", 0.2))
    ping_interval = int(getattr(settings, "SSE_PING_INTERVAL_SEC", 5))
    next_heartbeat = loop.time() + ping_interval

    # Send initial connection message to establish SSE stream
    yield 'event: connected\ndata: {"message": "SSE stream connected"}\n\n'

    iteration_count = 0
    logger.debug(f"SSE stream started for topic_id={topic_id}, lecture_id={lecture_id}")

    # Create a task to read events without blocking the main loop
    event_queue: asyncio.Queue = asyncio.Queue()
    reader_task = asyncio.create_task(_event_reader(events, event_queue))

    try:
        while True:
            iteration_count += 1

            # Send keepalive to maintain connection
            yield f": keepalive {iteration_count}\n\n"

            # Check for events without blocking
            try:
                ev = event_queue.get_nowait()
                if ev is _STREAM_CLOSED:
                    logger.debug("SSE stream closed - hub shutdown")
                    break

                if _event_matches(
                    ev, lecture_id=lecture_id, topic_id=topic_id, kinds_set=kinds_set
                ):
                    yield f"event: job\ndata: {json.dumps(ev, default=str)}\n\n"
            except asyncio.QueueEmpty:
                pass

            # Send periodic ping events
            now = loop.time()
            if now >= next_heartbeat:
                yield f"event: ping\ndata: {json.dumps({'time': now})}\n\n"
                next_heartbeat = now + ping_interval

            await asyncio.sleep(keepalive_interval)

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
        raise
    finally:
        # Clean up the reader task
        if "reader_task" in locals() and not reader_task.done():
            reader_task.cancel()
            try:
                await reader_task
            except asyncio.CancelledError:
                pass
        # Attempt to close the hub subscription generator
        try:
            await events.aclose()  # type: ignore[attr-defined]
        except Exception:
            pass
