import asyncio
import logging
import os
import signal
import tracemalloc
from typing import Any, Optional

logger = logging.getLogger("artificial_u.api.tracemalloc")


class TracemallocDriftTracer:
    """
    One-off memory drift tracer.

    When enabled:
    - start tracemalloc
    - take a baseline snapshot on startup (after worker start)
    - on SIGUSR1, take a new snapshot and log the top N allocation deltas vs baseline
    """

    def __init__(self, *, top_n: int = 25, max_frames: int = 25, traceback_top_n: int = 5) -> None:
        self.top_n = top_n
        self.max_frames = max_frames
        self.traceback_top_n = traceback_top_n
        self._baseline: Optional[tracemalloc.Snapshot] = None

    def start(self) -> None:
        if not tracemalloc.is_tracing():
            tracemalloc.start(self.max_frames)

    def set_baseline(self) -> None:
        self._baseline = tracemalloc.take_snapshot()
        logger.info("tracemalloc baseline captured", extra={"worker_pid": os.getpid()})

    def log_diff(self) -> None:
        if self._baseline is None:
            logger.warning("tracemalloc baseline missing; capturing now")
            self.set_baseline()
            return

        current = tracemalloc.take_snapshot()
        stats = current.compare_to(self._baseline, "lineno")

        logger.info(
            "tracemalloc diff (top %d vs baseline)",
            self.top_n,
            extra={"worker_pid": os.getpid()},
        )
        for i, stat in enumerate(stats[: self.top_n], start=1):
            frame = stat.traceback[0] if stat.traceback else None
            where = (
                f"{frame.filename}:{frame.lineno}" if frame is not None else "(unknown location)"
            )
            logger.info(
                "tracemalloc #%d %s size_diff=%dB count_diff=%d",
                i,
                where,
                stat.size_diff,
                stat.count_diff,
                extra={"worker_pid": os.getpid()},
            )
            if i <= self.traceback_top_n and stat.traceback:
                tb = "".join(stat.traceback.format())
                logger.info(
                    "tracemalloc #%d traceback:\n%s",
                    i,
                    tb.rstrip(),
                    extra={"worker_pid": os.getpid()},
                )


def tracemalloc_enabled() -> bool:
    return os.environ.get("DIAG_TRACEMALLOC", "").strip() == "1"


def install_tracemalloc_sigusr1_handler(app: Any, tracer: TracemallocDriftTracer) -> None:
    """
    Install a SIGUSR1 handler that schedules an async-safe diff log.

    Note: only works on POSIX (Linux/macOS). No-op on platforms without SIGUSR1.
    """
    if not hasattr(signal, "SIGUSR1"):
        return

    loop = asyncio.get_running_loop()

    def _on_sigusr1() -> None:
        # Schedule on the event loop thread.
        loop.call_soon_threadsafe(tracer.log_diff)

    try:
        loop.add_signal_handler(signal.SIGUSR1, _on_sigusr1)
        logger.info(
            "SIGUSR1 handler installed for tracemalloc diffs", extra={"worker_pid": os.getpid()}
        )
    except NotImplementedError:
        # Some environments (notably Windows) don't support this.
        return
