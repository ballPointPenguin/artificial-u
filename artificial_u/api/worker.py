import asyncio
import ctypes
import gc
import logging
import os
import sys
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from aiolimiter import AsyncLimiter  # type: ignore

from artificial_u.api.config import get_settings
from artificial_u.api.events import JobEventHub
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.job_service import JobService

Handler = Callable[[Dict[str, Any], RepositoryFactory], Awaitable[Dict[str, Any]]]


def _job_log_extra(
    *,
    job_id: int,
    kind: str,
    attempt: int,
    max_attempts: Optional[int] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Structured fields for CloudWatch Logs Insights (task 1.2)."""
    extra: Dict[str, Any] = {
        "job_id": job_id,
        "kind": kind,
        "attempt": attempt,
        "worker_pid": os.getpid(),
    }
    if max_attempts is not None:
        extra["max_attempts"] = max_attempts
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    return extra


def _telemetry_result(duration_ms: int) -> Dict[str, Any]:
    return {"_job_telemetry": {"duration_ms": duration_ms, "worker_pid": os.getpid()}}


def _with_job_telemetry(result: Dict[str, Any], duration_ms: int) -> Dict[str, Any]:
    out = dict(result) if result else {}
    out["_job_telemetry"] = {"duration_ms": duration_ms, "worker_pid": os.getpid()}
    return out


class Worker:
    def __init__(self, repository_factory: RepositoryFactory, event_hub: JobEventHub | None = None):
        self.settings = get_settings()
        self.repository_factory = repository_factory
        self.limiter = AsyncLimiter(self.settings.OUTBOUND_RPS, 1)
        self.semaphore = asyncio.Semaphore(self.settings.WORKER_MAX_CONCURRENCY)
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()
        self.job_service = JobService(repository_factory)
        self.logger = logging.getLogger("artificial_u.api.worker")
        self.event_hub = event_hub
        # If set to a positive int, logs an idle message every N polling cycles.
        # Default is 0 (disabled) to avoid log spam during development.
        self._idle_log_every = int(os.environ.get("WORKER_IDLE_LOG_EVERY", "0"))

    async def start(self):
        if self._task and not self._task.done():
            self.logger.info("Worker task already running, skipping start")
            return
        self.logger.info(
            "Starting worker with settings: poll_idle=%.2fs, visibility_timeout=%ds, "
            "max_concurrency=%d, outbound_rps=%d",
            self.settings.WORKER_POLL_IDLE_SEC,
            self.settings.WORKER_VISIBILITY_TIMEOUT_SEC,
            self.settings.WORKER_MAX_CONCURRENCY,
            self.settings.OUTBOUND_RPS,
        )
        self._stopped.clear()
        self._task = asyncio.create_task(self._run_loop())
        self.logger.info("Worker started successfully")

    async def stop(self):
        self.logger.info("Stopping worker...")
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Worker stopped")

    async def _run_loop(self):  # noqa: C901
        repo = self.repository_factory.job
        self.logger.info("Worker loop started")
        loop_count = 0
        running: Set[asyncio.Task] = set()
        _last_sweep = 0.0
        # Sweep at most once per minute; visibility timeout is 35 min so this is plenty.
        _sweep_interval = 60.0

        while not self._stopped.is_set():
            loop_count += 1
            try:
                await self._cooperative_yield()

                now_mono = time.monotonic()
                if now_mono - _last_sweep >= _sweep_interval:
                    await self._sweep_stuck_jobs(repo)
                    _last_sweep = now_mono

                # Fill any open concurrency slots immediately.
                available = self.settings.WORKER_MAX_CONCURRENCY - len(running)
                if available > 0:
                    new_tasks = await self._reserve_jobs(repo, limit=available)
                    if new_tasks:
                        self.logger.info(
                            f"Starting {len(new_tasks)} new job(s); "
                            f"{len(running) + len(new_tasks)} total running"
                        )
                    running.update(new_tasks)

                if running:
                    # Wake as soon as any task finishes so we can refill the slot.
                    done, running = await asyncio.wait(
                        running,
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=self.settings.WORKER_POLL_IDLE_SEC,
                    )
                    if done:
                        self.logger.debug(
                            f"{len(done)} job(s) completed, {len(running)} still running"
                        )
                else:
                    await self._idle_or_log(loop_count)
            except asyncio.CancelledError:
                self.logger.info("Worker loop cancelled, shutting down")
                try:
                    if running:
                        await self._cancel_pending(list(running))
                except Exception:
                    pass
                raise
            except Exception as e:
                self.logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(2.0)

        self.logger.info("Worker loop stopped")

    async def _cooperative_yield(self) -> None:
        """Yield control to the event loop to remain responsive to cancellation."""
        await asyncio.sleep(0)

    async def _sweep_stuck_jobs(self, repo) -> None:
        """Sweep stuck jobs with a small timeout; log outcomes without raising."""
        try:
            swept_count = await asyncio.wait_for(
                asyncio.to_thread(
                    repo.sweep_stuck,
                    visibility_timeout_seconds=self.settings.WORKER_VISIBILITY_TIMEOUT_SEC,
                ),
                timeout=5.0,
            )
            if swept_count > 0:
                self.logger.warning(f"Swept {swept_count} stuck jobs back to queued status")
        except asyncio.TimeoutError:
            self.logger.warning("Database operation timed out during sweep")

    async def _reserve_jobs(self, repo, limit: int | None = None) -> list[asyncio.Task]:
        """Reserve up to limit (or WORKER_MAX_CONCURRENCY) jobs, returning tasks."""
        max_count = limit if limit is not None else self.settings.WORKER_MAX_CONCURRENCY
        tasks: list[asyncio.Task] = []
        for _ in range(max_count):
            if self._stopped.is_set():
                break
            try:
                row = await asyncio.wait_for(
                    asyncio.to_thread(repo.reserve_one_skip_locked_atomic),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                self.logger.warning("Job reservation timed out")
                break

            if not row:
                break

            self.logger.info(
                "Job reserved",
                extra=_job_log_extra(
                    job_id=row.id,
                    kind=row.kind,
                    attempt=row.attempts,
                    max_attempts=row.max_attempts,
                    duration_ms=0,
                ),
            )
            tasks.append(asyncio.create_task(self._run_one(row.id)))
        return tasks

    async def _cancel_pending(self, tasks: list[asyncio.Task]) -> None:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _idle_or_log(self, loop_count: int) -> None:
        """Log occasionally when idle and sleep briefly while remaining cancellable."""
        if self._idle_log_every > 0 and loop_count % self._idle_log_every == 0:
            self.logger.debug(f"No jobs found after {loop_count} polling cycles")
        if self._stopped.is_set():
            return
        try:
            await asyncio.wait_for(
                asyncio.sleep(self.settings.WORKER_POLL_IDLE_SEC),
                timeout=self.settings.WORKER_POLL_IDLE_SEC,
            )
        except asyncio.TimeoutError:
            # This shouldn't happen, but handle it just in case
            pass

    async def _run_one(self, job_id: int):
        repo = self.repository_factory.job
        row = await asyncio.to_thread(repo.get, job_id)
        if not row:
            self.logger.warning(
                "Job not found for processing",
                extra={"job_id": job_id, "worker_pid": os.getpid()},
            )
            return

        kind = row.kind
        payload = row.payload or {}
        attempts = row.attempts
        max_attempts = row.max_attempts

        async with self.semaphore:
            exec_t0 = time.perf_counter()

            def execution_ms() -> int:
                return int((time.perf_counter() - exec_t0) * 1000)

            log_base = _job_log_extra(
                job_id=job_id,
                kind=kind,
                attempt=attempts,
                max_attempts=max_attempts,
            )
            self.logger.info(
                "Job execution start",
                extra={**log_base, "duration_ms": 0},
            )

            # If the job was cancelled after reservation, honor cancellation
            if row.status == "cancelled":
                self.logger.info(
                    "Job cancelled before execution",
                    extra={**log_base, "duration_ms": execution_ms()},
                )
                await self._publish_event(job_id, kind, "cancelled", payload)
                return
            try:
                result = await self._execute_job(job_id, kind, payload, log_base)
            except asyncio.TimeoutError:
                await self._handle_timeout(
                    repo,
                    job_id,
                    kind,
                    payload,
                    attempts,
                    max_attempts,
                    duration_ms=execution_ms(),
                )
                return
            except Exception as e:  # noqa: BLE001
                await self._handle_exception(
                    repo,
                    job_id,
                    kind,
                    payload,
                    attempts,
                    max_attempts,
                    e,
                    duration_ms=execution_ms(),
                )
                return

            duration_ms = execution_ms()
            result = _with_job_telemetry(result, duration_ms)

            # Success path
            await asyncio.to_thread(repo.mark_done, job_id, result)
            self.logger.info(
                "Job done",
                extra={**log_base, "duration_ms": duration_ms},
            )

            # Check for follow-up action and enqueue next job if present
            await self._handle_follow_up(kind, payload)

            await self._publish_event(job_id, kind, "done", payload, result=result)

            self._post_job_cleanup(kind)

    def _post_job_cleanup(self, kind: str) -> None:
        """Release glibc arenas and Python cyclic garbage after heavy jobs."""
        gc.collect()
        if sys.platform == "linux":
            try:
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            except Exception:
                pass
        self.logger.debug("Post-job cleanup done", extra={"kind": kind})

    async def _execute_job(
        self,
        job_id: int,
        kind: str,
        payload: Dict[str, Any],
        log_base: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a single job under rate-limit, publish running, and return result."""
        async with self.limiter:
            self.logger.debug("Dispatching job to handler", extra={**log_base, "job_id": job_id})
            await self._publish_event(job_id, kind, "running", payload)
            result = await asyncio.wait_for(
                self.job_service.dispatch(kind, payload, parent_job_id=job_id),
                timeout=self.settings.JOB_EXECUTION_TIMEOUT_SEC,
            )
            return result

    async def _handle_timeout(
        self,
        repo,
        job_id: int,
        kind: str,
        payload: Dict[str, Any],
        attempts: int,
        max_attempts: int,
        *,
        duration_ms: int,
    ) -> None:
        error_msg = (
            f"Job {job_id} timed out after {self.settings.JOB_EXECUTION_TIMEOUT_SEC} seconds"
        )
        extra = _job_log_extra(
            job_id=job_id,
            kind=kind,
            attempt=attempts,
            max_attempts=max_attempts,
            duration_ms=duration_ms,
        )
        self.logger.error(error_msg, extra=extra)
        delay = self.job_service.compute_backoff_seconds(attempts)
        telem = _telemetry_result(duration_ms)
        await asyncio.to_thread(
            repo.mark_failed_or_retry,
            job_id,
            attempts,
            max_attempts,
            last_error=error_msg,
            delay_seconds=delay,
            result=telem,
        )
        await self._publish_event(
            job_id,
            kind,
            "queued" if attempts < max_attempts else "failed",
            payload,
            last_error=error_msg,
            result=telem,
        )

    async def _handle_exception(
        self,
        repo,
        job_id: int,
        kind: str,
        payload: Dict[str, Any],
        attempts: int,
        max_attempts: int,
        exc: Exception,
        *,
        duration_ms: int,
    ) -> None:
        error_msg = f"Job {job_id} failed: {str(exc)}"
        extra = _job_log_extra(
            job_id=job_id,
            kind=kind,
            attempt=attempts,
            max_attempts=max_attempts,
            duration_ms=duration_ms,
        )
        self.logger.error(error_msg, exc_info=True, extra=extra)
        delay = self.job_service.compute_backoff_seconds(attempts)

        if attempts < max_attempts:
            self.logger.info(
                "Job will retry",
                extra={
                    **extra,
                    "retry_in_sec": round(delay, 2),
                    "next_attempt": attempts + 1,
                },
            )

        telem = _telemetry_result(duration_ms)
        await asyncio.to_thread(
            repo.mark_failed_or_retry,
            job_id,
            attempts,
            max_attempts,
            last_error=str(exc),
            delay_seconds=delay,
            result=telem,
        )
        await self._publish_event(
            job_id,
            kind,
            "queued" if attempts < max_attempts else "failed",
            payload,
            last_error=str(exc),
            result=telem,
        )

    async def _publish_event(
        self,
        job_id: int,
        kind: str,
        status: str,
        payload: Dict[str, Any],
        *,
        result: Dict[str, Any] | None = None,
        last_error: str | None = None,
    ) -> None:
        if not self.event_hub:
            return
        try:
            event: Dict[str, Any] = {
                "id": job_id,
                "kind": kind,
                "status": status,
                "payload": payload,
            }
            if result is not None:
                event["result"] = result
            if last_error is not None:
                event["last_error"] = last_error
            await self.event_hub.publish(event)
        except Exception:  # noqa: BLE001
            # Never fail the worker due to SSE publish errors
            pass

    async def _handle_follow_up(self, kind: str, payload: Dict[str, Any]) -> None:
        """
        Handle follow-up actions after job completion.

        If payload contains a 'follow_up' field, this creates the next job in the series.
        This enables serial batch processing without a full queue system.

        Follow-up structure:
        {
            "action": "generate_lecture" | "generate_lecture_audio" | "generate_lecture_timeline",
            "remaining_topic_ids": [4, 5, 6, ...],
            "course_id": 10,
            "created_by": "user@example.com",
            "partial_attributes": {...}  # optional, for lecture generation
        }
        """
        follow_up = payload.get("follow_up")
        if not follow_up:
            return

        # IMPORTANT: For batched lecture generation, we intentionally chain via the
        # `generate_lecture_summary` job (which is enqueued by the lecture generation handler).
        # That ensures each subsequent lecture prompt includes the fully-updated summary context
        # from the prior lecture.
        if kind == "generate_lecture":
            self.logger.info(
                "Skipping direct follow-up enqueue for generate_lecture; chaining occurs after summary"
            )
            return

        remaining_topic_ids = follow_up.get("remaining_topic_ids", [])
        if not remaining_topic_ids:
            self.logger.info("Batch complete: no remaining topic IDs in follow_up")
            return

        # Pop the first topic ID for the next job
        next_topic_id = remaining_topic_ids[0]
        new_remaining = remaining_topic_ids[1:]

        action = follow_up.get("action")
        if not action:
            self.logger.warning("Follow-up missing 'action' field, skipping")
            return

        self.logger.info(
            f"Enqueueing follow-up job: action={action}, topic_id={next_topic_id}, "
            f"remaining={len(new_remaining)}"
        )

        # Build the next job's payload based on action type
        next_payload = await self._build_follow_up_payload(
            action, next_topic_id, follow_up, new_remaining
        )
        if next_payload is None:
            # If payload building failed (e.g., missing lecture), continue with remaining topics
            if new_remaining:
                await self._enqueue_next_in_chain(action, new_remaining, follow_up)
            return

        # Enqueue the next job
        await self._enqueue_follow_up_job(action, next_payload, next_topic_id)

    async def _build_follow_up_payload(
        self,
        action: str,
        next_topic_id: int,
        follow_up: Dict[str, Any],
        new_remaining: list[int],
    ) -> Dict[str, Any] | None:
        """Build payload for the next job in the follow-up chain."""
        if action == "generate_lecture":
            return self._build_lecture_payload(next_topic_id, follow_up, new_remaining)
        elif action == "generate_lecture_audio":
            return await self._build_audio_payload(next_topic_id, follow_up, new_remaining)
        elif action == "generate_lecture_timeline":
            return await self._build_timeline_payload(next_topic_id, follow_up, new_remaining)
        else:
            self.logger.warning(f"Unknown follow-up action: {action}")
            return None

    def _build_lecture_payload(
        self,
        next_topic_id: int,
        follow_up: Dict[str, Any],
        new_remaining: list[int],
    ) -> Dict[str, Any]:
        """Build payload for lecture generation follow-up job."""
        # Make a copy to avoid mutating the original follow_up dict
        partial_attrs = follow_up.get("partial_attributes", {}).copy()
        partial_attrs["topic_id"] = next_topic_id

        payload = {
            "partial_attributes": partial_attrs,
            "freeform_prompt": follow_up.get("freeform_prompt"),
            "created_by": follow_up.get("created_by"),
        }

        if new_remaining:
            # Create new follow_up with copied partial_attributes to avoid mutation
            new_follow_up = {
                "action": follow_up.get("action"),
                "course_id": follow_up.get("course_id"),
                "created_by": follow_up.get("created_by"),
                "partial_attributes": follow_up.get("partial_attributes", {}).copy(),
                "remaining_topic_ids": new_remaining,
            }
            if "freeform_prompt" in follow_up:
                new_follow_up["freeform_prompt"] = follow_up["freeform_prompt"]
            payload["follow_up"] = new_follow_up

        return payload

    async def _build_audio_payload(
        self,
        next_topic_id: int,
        follow_up: Dict[str, Any],
        new_remaining: list[int],
    ) -> Dict[str, Any] | None:
        """Build payload for audio generation follow-up job."""
        course_id = follow_up.get("course_id")
        if not course_id:
            self.logger.error("Follow-up audio generation missing course_id")
            return None

        # Query for the lecture with this topic_id
        try:
            lecture_repo = self.repository_factory.lecture
            lectures = await asyncio.to_thread(lecture_repo.list_by_topic, next_topic_id)
            if not lectures or len(lectures) == 0:
                self.logger.warning(
                    f"No lecture found for topic {next_topic_id}, skipping audio generation"
                )
                # Return None to let caller handle continuation with remaining topics
                return None

            payload: Dict[str, Any] = {
                "lecture_id": lectures[0].id,
                "topic_id": next_topic_id,
            }

            if new_remaining:
                payload["follow_up"] = {
                    **follow_up,
                    "remaining_topic_ids": new_remaining,
                }

            return payload
        except Exception as e:
            self.logger.error(f"Error querying lecture for topic {next_topic_id}: {e}")
            return None

    async def _build_timeline_payload(
        self,
        next_topic_id: int,
        follow_up: Dict[str, Any],
        new_remaining: list[int],
    ) -> Dict[str, Any] | None:
        """Build payload for timeline generation follow-up job."""
        course_id = follow_up.get("course_id")
        if not course_id:
            self.logger.error("Follow-up timeline generation missing course_id")
            return None

        # Query for the lecture with this topic_id
        try:
            lecture_repo = self.repository_factory.lecture
            lectures = await asyncio.to_thread(lecture_repo.list_by_topic, next_topic_id)
            if not lectures or len(lectures) == 0:
                self.logger.warning(
                    f"No lecture found for topic {next_topic_id}, skipping timeline generation"
                )
                return None

            lecture = lectures[0]
            if not getattr(lecture, "audio_url", None):
                self.logger.warning(
                    f"No lecture audio found for topic {next_topic_id}, skipping timeline generation"
                )
                return None

            payload: Dict[str, Any] = {
                "lecture_id": lecture.id,
                "topic_id": next_topic_id,
            }

            if new_remaining:
                payload["follow_up"] = {
                    **follow_up,
                    "remaining_topic_ids": new_remaining,
                }

            return payload
        except Exception as e:
            self.logger.error(f"Error querying lecture for topic {next_topic_id}: {e}")
            return None

    async def _enqueue_follow_up_job(
        self,
        action: str,
        next_payload: Dict[str, Any],
        next_topic_id: int,
    ) -> None:
        """Enqueue the follow-up job.

        Priority is derived from the job kind (see ``job_priorities``), so it
        stays consistent across the whole follow-up chain.
        """
        try:
            repo = self.repository_factory.job
            next_job = await asyncio.to_thread(
                repo.create,
                kind=action,
                payload=next_payload,
            )
            self.logger.info(
                f"Enqueued follow-up job {next_job.id}: {action} for topic {next_topic_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to enqueue follow-up job: {e}", exc_info=True)

    async def _enqueue_next_in_chain(
        self,
        action: str,
        remaining_topic_ids: list[int],
        follow_up: Dict[str, Any],
    ) -> None:
        """Helper to enqueue next job when current one is skipped."""
        if not remaining_topic_ids:
            return

        next_topic_id = remaining_topic_ids[0]
        new_remaining = remaining_topic_ids[1:]

        # Build payload using the shared helper
        next_payload = await self._build_follow_up_payload(
            action, next_topic_id, follow_up, new_remaining
        )
        if next_payload is None:
            # If payload building failed (e.g., missing lecture), recursively try next in chain
            if new_remaining:
                await self._enqueue_next_in_chain(action, new_remaining, follow_up)
            return

        # Enqueue the job (priority is derived from the job kind)
        await self._enqueue_follow_up_job(action, next_payload, next_topic_id)
