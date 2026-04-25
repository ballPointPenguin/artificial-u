import asyncio
import gc
import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("artificial_u.api.telemetry")


def _safe_int(val: Any) -> Optional[int]:
    try:
        return int(val)
    except Exception:
        return None


def _get_rss_bytes_fallback() -> Optional[int]:
    """
    Best-effort RSS bytes without third-party dependencies.

    Preference order:
    - Linux procfs: /proc/self/status (VmRSS)
    - resource.getrusage (platform-dependent units)
    """
    # Linux procfs path (works in ECS)
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    # e.g. "VmRSS:\t  123456 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        kb = _safe_int(parts[1])
                        if kb is not None:
                            return kb * 1024
                    break
    except Exception:
        pass

    # Fallback: resource.getrusage (ru_maxrss)
    try:
        import resource

        ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is kilobytes. On macOS, it is bytes.
        if sys.platform.startswith("linux"):
            return int(ru_maxrss) * 1024
        return int(ru_maxrss)
    except Exception:
        return None


def _get_num_fds() -> Optional[int]:
    # Works on Linux and macOS.
    try:
        return len(os.listdir("/proc/self/fd"))
    except Exception:
        pass
    try:
        return len(os.listdir("/dev/fd"))
    except Exception:
        return None


def _get_psutil_metrics() -> Dict[str, Any]:
    """
    psutil-backed metrics when available.

    psutil is a declared dependency, but we still treat failures as non-fatal
    so telemetry never breaks startup.
    """
    try:
        import psutil  # type: ignore

        p = psutil.Process()
        mi = p.memory_info()
        return {
            "rss_bytes": int(getattr(mi, "rss", 0) or 0),
            "vms_bytes": int(getattr(mi, "vms", 0) or 0),
            "num_threads": int(p.num_threads()),
            "num_fds": int(p.num_fds()) if hasattr(p, "num_fds") else None,
        }
    except Exception:
        return {}


async def _get_worker_metrics(app: Any) -> Dict[str, Any]:
    worker = getattr(getattr(app, "state", None), "worker", None)
    if worker is None:
        return {"worker_present": False}

    sem = getattr(worker, "semaphore", None)
    max_conc = getattr(getattr(worker, "settings", None), "WORKER_MAX_CONCURRENCY", None)
    available = getattr(sem, "_value", None) if sem is not None else None
    in_use = None
    if max_conc is not None and available is not None:
        try:
            in_use = int(max_conc) - int(available)
        except Exception:
            in_use = None

    return {
        "worker_present": True,
        "worker_max_concurrency": _safe_int(max_conc),
        "worker_semaphore_available": _safe_int(available),
        "worker_semaphore_in_use": _safe_int(in_use),
    }


async def _get_sse_metrics(app: Any) -> Dict[str, Any]:
    hub = getattr(getattr(app, "state", None), "job_events", None)
    if hub is None:
        return {"sse_subscribers": None}
    try:
        count = await hub.subscriber_count()
        return {"sse_subscribers": int(count)}
    except Exception:
        return {"sse_subscribers": None}


def _get_gc_metrics() -> Dict[str, Any]:
    # gc.get_stats() exists on modern Python; guard just in case.
    stats = None
    try:
        stats = gc.get_stats()
    except Exception:
        stats = None

    return {
        "gc_enabled": bool(gc.isenabled()),
        "gc_counts": list(gc.get_count()),
        "gc_stats": stats,
        "gc_thresholds": list(gc.get_threshold()),
    }


async def process_telemetry_loop(app: Any, *, interval_sec: float) -> None:
    """
    Periodically log per-process telemetry as a single JSON object.

    Enabled by env var in app lifespan to avoid overhead by default.
    """
    pid = os.getpid()
    ppid = os.getppid()

    while True:
        now = datetime.now(timezone.utc).isoformat()

        psutil_metrics = _get_psutil_metrics()
        rss_bytes = psutil_metrics.get("rss_bytes") or _get_rss_bytes_fallback()
        vms_bytes = psutil_metrics.get("vms_bytes")
        num_threads = psutil_metrics.get("num_threads") or threading.active_count()
        num_fds = psutil_metrics.get("num_fds") or _get_num_fds()

        payload: Dict[str, Any] = {
            "ts": now,
            "pid": pid,
            "ppid": ppid,
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "rss_bytes": rss_bytes,
            "vms_bytes": vms_bytes,
            "num_threads": num_threads,
            "num_fds": num_fds,
            **_get_gc_metrics(),
        }

        payload.update(await _get_sse_metrics(app))
        payload.update(await _get_worker_metrics(app))

        logger.info("process_telemetry %s", json.dumps(payload, default=str, ensure_ascii=False))
        await asyncio.sleep(interval_sec)
