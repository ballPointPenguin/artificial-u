import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiolimiter import AsyncLimiter  # type: ignore

from artificial_u.api.config import get_settings
from artificial_u.api.events import JobEventHub
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.job_service import JobService

Handler = Callable[[Dict[str, Any], RepositoryFactory], Awaitable[Dict[str, Any]]]


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

    async def _run_loop(self):
        repo = self.repository_factory.job
        self.logger.info("Worker loop started")
        loop_count = 0

        while not self._stopped.is_set():
            loop_count += 1
            try:
                await self._cooperative_yield()
                await self._sweep_stuck_jobs(repo)
                tasks = await self._reserve_jobs(repo)
                if tasks:
                    await self._process_tasks(tasks)
                else:
                    await self._idle_or_log(loop_count)
            except asyncio.CancelledError:
                self.logger.info("Worker loop cancelled, shutting down")
                # Best-effort cancellation of any tasks created in this iteration
                try:
                    if "tasks" in locals() and tasks:
                        await self._cancel_pending(tasks)
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

    async def _reserve_jobs(self, repo) -> list[asyncio.Task]:
        """Reserve up to max concurrency jobs, returning tasks to process them."""
        tasks: list[asyncio.Task] = []
        for _ in range(self.settings.WORKER_MAX_CONCURRENCY):
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

            self.logger.info(f"Reserved job {row.id} (kind: {row.kind})")
            tasks.append(asyncio.create_task(self._run_one(row.id)))
        return tasks

    async def _process_tasks(self, tasks: list[asyncio.Task]) -> None:
        """Process tasks with an optional timeout and cancel any that overrun."""
        self.logger.info(f"Processing {len(tasks)} jobs concurrently")
        timeout = self.settings.WORKER_TASKS_PROCESSING_TIMEOUT_SEC
        try:
            if timeout is None or timeout <= 0:
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout,
                )
        except asyncio.TimeoutError:
            self.logger.warning("Concurrent task batch timed out, cancelling remaining tasks")
            await self._cancel_pending(tasks)

    async def _cancel_pending(self, tasks: list[asyncio.Task]) -> None:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _idle_or_log(self, loop_count: int) -> None:
        """Log occasionally when idle and sleep briefly while remaining cancellable."""
        if loop_count % 40 == 0:
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
            self.logger.warning(f"Job {job_id} not found when trying to process")
            return

        kind = row.kind
        payload = row.payload or {}
        attempts = row.attempts
        max_attempts = row.max_attempts

        self.logger.info(
            f"Starting job {job_id} (kind: {kind}, attempt: {attempts}/{max_attempts})"
        )

        async with self.semaphore:
            # If the job was cancelled after reservation, honor cancellation
            if row.status == "cancelled":
                self.logger.info(f"Job {job_id} was cancelled before execution")
                await self._publish_event(job_id, kind, "cancelled", payload)
                return
            try:
                result = await self._execute_job(job_id, kind, payload)
            except asyncio.TimeoutError:
                await self._handle_timeout(repo, job_id, kind, payload, attempts, max_attempts)
                return
            except Exception as e:  # noqa: BLE001
                await self._handle_exception(repo, job_id, kind, payload, attempts, max_attempts, e)
                return

            # Success path
            await asyncio.to_thread(repo.mark_done, job_id, result)
            self.logger.info(f"Job {job_id} marked as done")

            # Check for follow-up action and enqueue next job if present
            await self._handle_follow_up(payload, kind, result)

            await self._publish_event(job_id, kind, "done", payload, result=result)

    async def _execute_job(self, job_id: int, kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single job under rate-limit, publish running, and return result."""
        async with self.limiter:
            self.logger.debug(f"Dispatching job {job_id} to handler for kind: {kind}")
            await self._publish_event(job_id, kind, "running", payload)
            result = await asyncio.wait_for(
                self.job_service.dispatch(kind, payload),
                timeout=self.settings.JOB_EXECUTION_TIMEOUT_SEC,
            )
            self.logger.info(f"Job {job_id} completed successfully")
            return result

    async def _handle_timeout(
        self,
        repo,
        job_id: int,
        kind: str,
        payload: Dict[str, Any],
        attempts: int,
        max_attempts: int,
    ) -> None:
        error_msg = (
            f"Job {job_id} timed out after {self.settings.JOB_EXECUTION_TIMEOUT_SEC} seconds"
        )
        self.logger.error(error_msg)
        delay = self.job_service.compute_backoff_seconds(attempts)
        await asyncio.to_thread(
            repo.mark_failed_or_retry,
            job_id,
            attempts,
            max_attempts,
            last_error=error_msg,
            delay_seconds=delay,
        )
        await self._publish_event(
            job_id,
            kind,
            "queued" if attempts < max_attempts else "failed",
            payload,
            last_error=error_msg,
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
    ) -> None:
        error_msg = f"Job {job_id} failed: {str(exc)}"
        self.logger.error(error_msg, exc_info=True)
        delay = self.job_service.compute_backoff_seconds(attempts)

        if attempts >= max_attempts:
            self.logger.error(
                f"Job {job_id} reached max attempts ({max_attempts}), marking as failed"
            )
        else:
            next_attempt = attempts + 1
            self.logger.info(
                f"Job {job_id} will retry in {delay:.2f}s (attempt {next_attempt}/{max_attempts})"
            )

        await asyncio.to_thread(
            repo.mark_failed_or_retry,
            job_id,
            attempts,
            max_attempts,
            last_error=str(exc),
            delay_seconds=delay,
        )
        await self._publish_event(
            job_id,
            kind,
            "queued" if attempts < max_attempts else "failed",
            payload,
            last_error=str(exc),
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

    async def _handle_follow_up(
        self,
        payload: Dict[str, Any],
        completed_kind: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Handle follow-up actions after job completion.

        If payload contains a 'follow_up' field, this creates the next job in the series.
        This enables serial batch processing without a full queue system.

        Follow-up structure:
        {
            "action": "generate_lecture" | "generate_lecture_audio",
            "remaining_topic_ids": [4, 5, 6, ...],
            "course_id": 10,
            "created_by": "user@example.com",
            "partial_attributes": {...}  # optional, for lecture generation
        }
        """
        follow_up = payload.get("follow_up")
        if not follow_up:
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
        await self._enqueue_follow_up_job(
            action, next_payload, next_topic_id, payload.get("priority", 0)
        )

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
        partial_attrs = follow_up.get("partial_attributes", {})
        partial_attrs["topic_id"] = next_topic_id

        payload = {
            "partial_attributes": partial_attrs,
            "freeform_prompt": follow_up.get("freeform_prompt"),
            "created_by": follow_up.get("created_by"),
        }

        if new_remaining:
            payload["follow_up"] = {
                **follow_up,
                "remaining_topic_ids": new_remaining,
            }

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

            payload = {
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

    async def _enqueue_follow_up_job(
        self,
        action: str,
        next_payload: Dict[str, Any],
        next_topic_id: int,
        priority: int,
    ) -> None:
        """Enqueue the follow-up job."""
        try:
            repo = self.repository_factory.job
            next_job = await asyncio.to_thread(
                repo.create,
                kind=action,
                payload=next_payload,
                priority=priority,
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

        # Enqueue the job (using default priority of 0)
        await self._enqueue_follow_up_job(action, next_payload, next_topic_id, 0)
