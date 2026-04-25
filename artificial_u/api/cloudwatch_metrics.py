import asyncio
import logging
import os
from typing import Any, Dict, Iterable, List, Optional

import boto3

logger = logging.getLogger("artificial_u.api.cloudwatch_metrics")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip() in {"1", "true", "TRUE", "yes", "YES"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _metric(
    name: str,
    value: float,
    *,
    unit: str = "Count",
    dims: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    m: Dict[str, Any] = {"MetricName": name, "Value": float(value), "Unit": unit}
    if dims:
        m["Dimensions"] = dims
    return m


def _default_dimensions() -> List[Dict[str, str]]:
    env = os.environ.get("ENV", "unknown")
    service_role = os.environ.get("SERVICE_ROLE", "api")
    return [
        {"Name": "Env", "Value": env},
        {"Name": "ServiceRole", "Value": service_role},
    ]


async def cloudwatch_metrics_loop(app: Any, *, interval_sec: float) -> None:
    """
    Periodically emit CloudWatch custom metrics.

    Gated by env vars so it can be enabled only on one task/process.
    """
    namespace = os.environ.get("CLOUDWATCH_NAMESPACE", "ArtificialU")
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

    cw = boto3.client("cloudwatch", region_name=region)  # uses task role in ECS
    dims = _default_dimensions()

    repo_factory = getattr(getattr(app, "state", None), "repository_factory", None)
    hub = getattr(getattr(app, "state", None), "job_events", None)
    worker = getattr(getattr(app, "state", None), "worker", None)

    while True:
        try:
            metrics = await _collect_metrics(
                repo_factory=repo_factory, hub=hub, worker=worker, dims=dims
            )
            await _emit_metrics(cw=cw, namespace=namespace, metrics=metrics)
        except Exception as e:  # noqa: BLE001
            logger.warning("CloudWatch metrics emission failed: %s", e, exc_info=True)

        await asyncio.sleep(interval_sec)


async def _collect_metrics(
    *,
    repo_factory: Any,
    hub: Any,
    worker: Any,
    dims: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    metrics: List[Dict[str, Any]] = []
    metrics.extend(await _collect_job_metrics(repo_factory=repo_factory, dims=dims))
    metrics.extend(await _collect_sse_metrics(hub=hub, dims=dims))
    metrics.extend(_collect_worker_metrics(worker=worker, dims=dims))
    return metrics


async def _collect_job_metrics(
    *, repo_factory: Any, dims: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    if repo_factory is None:
        return []
    repo = repo_factory.job
    summary = await asyncio.to_thread(repo.telemetry_summary)
    counts: Dict[str, int] = summary.get("counts") or {}
    return [
        _metric("jobs.queued", counts.get("queued", 0), dims=dims),
        _metric("jobs.running", counts.get("running", 0), dims=dims),
        _metric("jobs.done", counts.get("done", 0), dims=dims),
        _metric("jobs.failed", counts.get("failed", 0), dims=dims),
        _metric("jobs.cancelled", counts.get("cancelled", 0), dims=dims),
        _metric("jobs.failed_last_hour", float(summary.get("failed_last_hour") or 0), dims=dims),
        _metric(
            "jobs.avg_wait_seconds",
            float(summary.get("avg_wait_seconds") or 0.0),
            unit="Seconds",
            dims=dims,
        ),
    ]


async def _collect_sse_metrics(*, hub: Any, dims: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    if hub is None:
        return []
    out: List[Dict[str, Any]] = []
    try:
        subs = await hub.subscriber_count()
        out.append(_metric("sse.active_streams", float(subs), dims=dims))
    except Exception:
        pass
    try:
        dropped = await hub.dropped_events_count()
        out.append(_metric("sse.publish_dropped", float(dropped), dims=dims))
    except Exception:
        pass
    return out


def _collect_worker_metrics(*, worker: Any, dims: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    if worker is None:
        return []
    sem = getattr(worker, "semaphore", None)
    max_conc = getattr(getattr(worker, "settings", None), "WORKER_MAX_CONCURRENCY", None)
    available = getattr(sem, "_value", None) if sem is not None else None
    if max_conc is None or available is None:
        return []
    try:
        in_use = float(int(max_conc) - int(available))
        return [_metric("worker.inflight", in_use, dims=dims)]
    except Exception:
        return []


async def _emit_metrics(*, cw: Any, namespace: str, metrics: List[Dict[str, Any]]) -> None:
    # CloudWatch PutMetricData supports up to 20 metrics per call.
    for chunk in _chunks(metrics, 20):
        if not chunk:
            continue
        await asyncio.to_thread(
            cw.put_metric_data,
            Namespace=namespace,
            MetricData=chunk,
        )


def _chunks(items: Iterable[Dict[str, Any]], n: int) -> List[List[Dict[str, Any]]]:
    out: List[List[Dict[str, Any]]] = []
    buf: List[Dict[str, Any]] = []
    for it in items:
        buf.append(it)
        if len(buf) >= n:
            out.append(buf)
            buf = []
    if buf:
        out.append(buf)
    return out


def cloudwatch_metrics_enabled() -> bool:
    """
    Enable CloudWatch metrics only when explicitly configured.

    To avoid duplicate emission under Gunicorn workers, require both:
      - DIAG_CLOUDWATCH_METRICS=1
      - DIAG_CLOUDWATCH_METRICS_LEADER=1
    """
    return _env_bool("DIAG_CLOUDWATCH_METRICS", False) and _env_bool(
        "DIAG_CLOUDWATCH_METRICS_LEADER", False
    )


def cloudwatch_metrics_interval_sec() -> float:
    return _env_float("DIAG_CLOUDWATCH_METRICS_INTERVAL_SEC", 60.0)
