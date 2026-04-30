# Background Jobs & Realtime — Evolution Plan

Plan for evolving the background job system, worker topology, and client-server
realtime communication as ArtificialU's workload grows in complexity (notably
lecture-image generation) without prematurely adopting heavy infrastructure.

Organized by priority: diagnostics first (cheap, inform later decisions), then
actionable work in near/medium/long-term buckets, then open questions we'll
revisit once we have data.

---

## Guiding principles

- Keep Postgres as the queue until we have evidence it can't keep up. `FOR UPDATE SKIP LOCKED` + a jobs table is sufficient for our scale.
- Prefer many small idempotent jobs over one long monolithic job.
- Separate serving from doing: request-handling and background work should not share the same process.
- Realtime mechanism should match the use case. The three distinct cases are:
  1. **Single-job "user waits for result"** → polling is simplest and most reliable.
  2. **Admin jobs dashboard** → SSE is justified (many events, live feel).
  3. **Cross-tab / cross-user coordination** → explicitly out of scope for now. Single-owner model mostly prevents clobbering; accept the edge case of admin + owner racing.
- Don't chase autoscaling until right-sizing and workload isolation are done.

---

## Category 1 — Diagnostics (do first; they inform everything else)

Low-effort instrumentation that makes later decisions evidence-based instead of
hunch-based. These are not blocked by anything and should land before the larger
refactors.

### 1.1 Process-level memory & GC telemetry - DONE

- Log structured JSON every 30–60s per process: `rss_mb`, `vms_mb`, `num_fds`, `num_threads`, `gc_counts`, `active_sse_streams`, `job_semaphore_in_use`.
- Use `psutil.Process()` + `gc.get_stats()`; gate behind `DIAG_PROCESS_METRICS=1` env var.
- Correlate via `pid` so you can see per-gunicorn-worker drift.

### 1.2 Job lifecycle structured logging - DONE

- Ensure every reserve/start/done/fail log line carries `extra={"job_id", "kind", "attempt", "duration_ms", "worker_pid"}`.
- Use CloudWatch Logs Insights to chart `avg(duration_ms) by kind`, `count() by status` by kind over time.

### 1.3 CloudWatch custom metrics (emitted from the app) - DONE

- `jobs.queued`, `jobs.running`, `jobs.failed_last_hour`, `jobs.avg_wait_seconds` (sourced from `summary_counts` + timing deltas).
- `sse.active_streams`, `sse.publish_dropped` (add a counter where `publish` hits a full queue).
- Emit via `boto3` `PutMetricData` on a 60s tick from a single worker task (avoid duplicate publishes across processes by gating on `pid == lowest_pid` or just tagging by pid and summing in CloudWatch).

### 1.4 CloudWatch alarms (informational, not paging) - TODO External

- Memory > 80% for 5 minutes on the Fargate task.
- `jobs.queued > 10` sustained 15 minutes.
- `jobs.failed_last_hour > 3`.

### 1.5 One-off memory drift trace - Code DONE, TODO Prod collection

- Add a `DIAG_TRACEMALLOC=1` toggle that snapshots on worker start and again on SIGUSR1, diffs top allocations, and logs the top 25.
- Run in prod for 24h during a quiet window to establish a baseline.

### 1.6 ECS Container Insights review - Done

- Already enabled per the recent screenshots. Save a dashboard bookmark that pins CPU, memory, network, and our custom metrics on one page so the whole team sees the same picture.

**Decision gates this unlocks:**

- "Is memory really leaking?" → from 1.1 and 1.5.
- "Should we raise Fargate task size or split services?" → from 1.3 + 1.4.
- "Which job kinds are the hotspots?" → from 1.2.

---

## Category 2 — Near-term actions (actionable now; low risk, high value)

Small, tactical changes that fix real bugs or avoid known foot-guns. Expected
to be completed in a handful of PRs without architectural disruption.

### 2.1 Fix the visibility-timeout / execution-timeout inversion (bug) - Simplest DONE

- Today: `WORKER_VISIBILITY_TIMEOUT_SEC=600` (10 min) but `JOB_EXECUTION_TIMEOUT_SEC=1800` (30 min). `sweep_stuck` will requeue a still-running image job after 10 min, letting a second worker pick it up concurrently and clobber S3 state.
- Options:
  - Simplest: raise `WORKER_VISIBILITY_TIMEOUT_SEC` above `JOB_EXECUTION_TIMEOUT_SEC` (e.g., 2100s).
  - Better: add a `JobRepository.heartbeat(job_id)` that sets `updated_at = now()` and call it periodically from inside long-running handlers.
- Pairs well with job splitting below, which naturally keeps individual tasks short enough that this doesn't matter.

### 2.2 Split lecture-image job into per-slide jobs - DONE

- Replace the single `generate_lecture_images` sequential loop in `artificial_u/services/lecture_images_generator_service.py` with:
  - `plan_lecture_images(lecture_id, ...)` — builds scaffold JSON, uploads initial timeline, enqueues N `generate_lecture_slide` jobs with a batch correlation key and low priority.
  - `generate_lecture_slide(lecture_id, slot_idx)` — single Gemini call + one S3 upload, per-slot idempotent.
  - `finalize_lecture_images(lecture_id, batch_id)` — optional aggregator that marks the batch complete when all slide jobs are `done|failed`.
- Benefits: each task ~10–30s, trivially retryable, naturally parallelizable, no wasted work on restart, no visibility-timeout risk.
- Schema note: we can encode the batch via `payload.batch_id` without a new table; reuse `priority` for slide jobs (e.g., priority `-10`).

### 2.3 Per-slot idempotency - DONE

- Before calling the image provider, check whether `slot_{idx}.png` (or the timeline slot's `url`) already exists and skip. Cheap win even before splitting.
- Lets retries cost $0 instead of $N.

### 2.4 SSE hygiene (without rearchitecting it yet) - DONE

- Pass `request` back into `sse_stream` in `artificial_u/api/routers/jobs.py:159` so `is_disconnected()` actually fires.
- Raise `SSE_KEEPALIVE_INTERVAL_SEC` from 0.2s to 1.0s; current rate is 5 ticks/sec/connection for no user benefit.
- Replace `put_nowait` silent drop in `JobEventHub.publish` with a counter that increments `sse.publish_dropped` metric, so dropped events are observable.
- When the client connects, emit a snapshot of the current job status so the UI can reconcile even if earlier events were missed.

### 2.5 Swap user-waits-for-result flows from SSE → polling - DONE

- For "user clicks generate, sees progress, waits for done" UX on known jobs, poll `GET /jobs/{id}` every 2s while status is `queued`/`running`, stop on terminal state.
- Keep SSE subscription only for the admin jobs dashboard (`web/src/pages/Jobs.tsx` via `/api/v1/jobs/stream`).
- Remove SSE use from single-job pages to simplify client code and remove cross-worker event-loss.
- Frontend implementation:
  - `web/src/utils/job-management.ts` now exposes `createJobPolling(jobId, options)` for single known-job flows.
  - `waitForJobResult(jobId)` shares the same polling defaults/error semantics for promise-style flows.
  - `createJobTracker()` is now explicit/local: components call `track(job.id)` after enqueueing jobs in the current browser tab session. It does not perform always-on entity polling.
  - `web/src/pages/Courses.tsx` uses `createJobPolling()` for create-course completion.
  - `web/src/pages/TopicDetail.tsx`, `web/src/pages/LectureDetail.tsx`, `web/src/components/lectures/LectureSection.tsx`, and `web/src/components/topics/CourseTopicsList.tsx` use local known-job tracking.
  - `web/src/pages/CourseDetail.tsx` no longer starts idle job polling for topic generation awareness.
- Cross-page continuity for downstream/child jobs is deferred to §3.5 and §3.6. The current short-term implementation intentionally avoids broad eager polling when the backend does not return child job IDs.

### 2.6 Reuse httpx clients - DONE

- Replace `async with httpx.AsyncClient()` in:
  - `artificial_u/services/lecture_images_generator_service.py:41`
  - `artificial_u/services/image_service.py:187,372`
  - (audit `share.py` routers too)
- Create a single `httpx.AsyncClient` per service instance, or a module-level singleton keyed by the process. Plug it into the DI factory in `artificial_u/api/dependencies.py` so tests can inject a mock.
- Minor memory/latency win, bigger correctness win (fewer TLS handshakes, consistent timeouts).

### 2.7 Priority lanes on the existing queue

- Use the existing `priority` column deliberately:
  - Interactive/"user waiting" jobs: priority `+10` (professor image, single lecture summary, single course creation).
  - Batch/slide jobs: priority `-10`.
- Small jobs can jump ahead of a 30-slide image batch that's been split into 30 queued jobs.

### 2.8 Tune Gunicorn for I/O-bound workload - DONE (stopgap)

- **2026-04-28**: Dropped `GUNICORN_WORKERS` from `2` to `1` in CDK (`cdk/cdk/cdk_stack.py`) after prod data showed two workers each plateauing at ~1 GB RSS → combined OOM-killed repeatedly at 97% memory. Single worker with 8 threads serves current traffic fine.
- Previous: `--workers 2 --threads 8` on 1 vCPU / 2 GiB. Two workers × ~1 GB steady-state = no headroom for a single timeline job spike.
- Proper fix: §3.1 (dedicated worker service). At that point we can right-size API small + worker bigger per §3.4.
- Parameter sweep is safe; revert-in-one-deploy.

### 2.9 Raise ECS `stopTimeout` to give workers a chance to finish

- In the CDK Fargate service, set `stopTimeout` to 120s (the max is 120s on Fargate) so the worker has real time to stop jobs gracefully on deploy.
- Update `Worker.stop()` to wait up to N seconds for in-flight `_run_one` tasks to complete before cancelling.
- Pairs with 2.2: short jobs finish in seconds, so graceful shutdown Just Works.

### 2.10 Stream large media in `StorageService` (don't hold full files in memory) - PARTIAL DONE

Confirmed by `tracemalloc` load-trace (single lecture run): the largest live allocation was ~24 MB at:

- `artificial_u/services/storage_service.py:349` → `return file_obj.read(), content_type` (≈24 MB, count_diff=1)

Local sizes during that run: lecture MP3 22.8 MiB, timeline JSON 464 KiB, lecture text 21.1 KiB. The MP3 explains the spike: the storage layer reads the entire object into memory.

**2026-04-28 prod data confirmed and sharpened this.** Per-worker memory-drift telemetry showed workers peaking at 1.0–1.3 GB RSS on `generate_lecture_timeline` jobs, then staying pinned there even at inflight=0. Root cause: `generate_lecture_timeline` called `storage_service.download_file()` (loads full MP3 bytes into Python heap) → passed those bytes to `client.forced_alignment()` (httpx wraps them again in a multipart body). Two copies of ~22 MB, neither released back to OS due to glibc malloc retention.

**Done (2026-04-28):**
- Added `StorageService.stream_to_tempfile_sync()` — streams S3 body in 1 MB chunks to a temp file with no Python heap spike.
- `generate_lecture_timeline` now calls `asyncio.to_thread(storage_service.stream_to_tempfile_sync, ...)` and passes the resulting path (not bytes) to `_generate_and_upload_timeline`. Temp file cleaned up in `finally` block.
- `_generate_and_upload_timeline` signature changed from `audio_bytes: bytes` → `audio_path: str`.
- `ElevenLabsClient.forced_alignment` signature changed from `audio_bytes: bytes` → `audio_path: str`. Opens the file in a `with` block; httpx streams it as multipart without an extra in-memory copy.

**Still to do:**
- Audit remaining `download_file` callers that return full bytes and convert where the consumer doesn't need the full buffer (e.g., audio serving HTTP responses, ID3 tagging).
- For ffmpeg integration, prefer piping (`stdin`/`stdout`) or temp files over loading the full MP3 into RAM.
- Avoid round-tripping audio bytes through Python just to compute metadata; use HEAD/`get_object_attributes` for size/content-type.

Expected impact:

- Eliminates the dominant memory spike on the `generate_lecture_timeline` path. RSS during a timeline job should stay flat instead of spiking +22 MB and pinning.
- Remaining `download_file` callers are smaller consumers; tackle them after observing 24h prod data.

### 2.11 Reuse boto3 clients/sessions - DONE

`tracemalloc` load-trace also shows large counts of `botocore` allocations, which is a classic signature of constructing botocore clients/models repeatedly on hot paths.

Actions:

- Ensure a single `boto3.Session` and single S3 client per process; reuse them in `StorageService`. Implemented via cached helpers in `artificial_u.integrations.aws_clients`.
- Audit any place that calls `boto3.client(...)` or instantiates a storage service per request/job and refactor to reuse.

Expected impact:

- Significant reduction in allocation churn and CPU time during storage-heavy sequences; minor RSS improvement.

### 2.12 Reduce JSON re-parse churn (timeline/alignment)

`json/decoder.py:361` showed a large allocation count during the lecture-generation run. With the timeline being 464 KiB, this is consistent with repeated parsing or repeated decode/encode round-trips.

Actions:

- Parse provider JSON once and pass the parsed dict between steps; avoid re-fetch+re-parse from S3/MinIO within the same job.
- Avoid `json.loads(json.dumps(...))` style round-trips on the hot path.
- Only consider streaming JSON parsers (e.g., `ijson`) if profiling shows the alignment output is a dominant CPU/memory cost.

Expected impact:

- Trims per-job allocation count and reduces GC noise during long generation jobs.

### 2.13 Limit glibc malloc arena retention — DONE (2026-04-28)

glibc's default `malloc` carves out one arena per CPU core (up to 8× cores). After a peak allocation each arena retains its mapped pages indefinitely, even when the memory is logically free. This is why RSS stays pinned at ~70% after the first wave of jobs, even at inflight=0.

**Done (2026-04-28):**
- Added `MALLOC_ARENA_MAX=2` to the ECS task environment in `cdk/cdk/cdk_stack.py`. Limits the allocator to two arenas regardless of core count.
- Added `Worker._post_job_cleanup()` called at the end of every successful job: runs `gc.collect()` to sweep CPython cyclic garbage, then calls `ctypes.CDLL("libc.so.6").malloc_trim(0)` (Linux only, wrapped in `try/except`) to prompt glibc to release free pages back to the OS.
- Imports added to `artificial_u/api/worker.py`: `ctypes`, `gc`, `sys`.

Expected impact:
- `MALLOC_ARENA_MAX=2` typically cuts steady-state RSS by 20–40% vs default on multi-threaded Python processes. Combined with `malloc_trim` after each job, RSS should return closer to baseline between batches.

### 2.14 In-process retry for Gemini transient errors — DONE (2026-04-28)

Google's `genai` SDK wraps requests with tenacity internally but only retries a narrow set of errors; HTTP 5xx `ServerError` responses (503 UNAVAILABLE, 500, 502, 504) propagate immediately. When a slide's image-generation handler receives a 503, it returns `status: "failed"` rather than raising an exception, so the job-level `compute_backoff_seconds` retry never fires. Slides hit by a transient 503 were permanently dead.

**Done (2026-04-28):**
- Added module-level `_is_gemini_transient_error(exc)` predicate in `artificial_u/services/image_service.py` — returns `True` for `ServerError` with status codes `{429, 500, 502, 503, 504}`.
- Wrapped the `_generate_gemini_image(...)` call inside `_generate_with_backend` with `tenacity.AsyncRetrying`: `stop_after_attempt(4)`, `wait_exponential(multiplier=2, min=2, max=30)`, `reraise=True`. Logs a warning before each sleep.
- `tenacity` was already in `requirements.txt` (9.1.4).

Expected impact:
- Transient 503/500 errors from Gemini are retried up to 3 more times (up to ~30 s back-off) before propagating. Slide batches that previously produced permanent failures during Google capacity events should now recover silently.

---

## Category 3 — Medium-term (meaningful refactor; depends on near-term landing first)

Bigger but still well-scoped changes. Each is a deliberate project once the
near-term cleanup and diagnostics are in.

### 3.1 Dedicated worker ECS service (same image)

- Add a `SERVICE_ROLE={api|worker|both}` env var.
  - `api`: skips `worker.start()`; runs FastAPI only.
  - `worker`: runs worker loop, optionally disables HTTP (or keeps a minimal `/health` endpoint).
  - `both`: current dev behavior for local convenience.
- In CDK: a second `ecs.FargateService` using the same `DockerImageAsset`, no ALB, its own `desired_count` and CPU/memory sizing. Postgres is still the queue — nothing else changes.
- Expected wins:
  - Heavy jobs can't starve HTTP threads.
  - We can right-size API small (low memory) and worker bigger (more memory for image bytes in flight).
  - Deploy cycles for API don't kill long jobs and vice versa.

### 3.2 Cross-process SSE for the admin dashboard (only)

Now that SSE is scoped to the admin dashboard (per 2.5), fix the multi-process
delivery gap properly:

- Option A: **Postgres `LISTEN/NOTIFY`**. Worker `NOTIFY job_events '<payload>'`; every API process has a single background task consuming `LISTEN job_events` and fanning out to its local `JobEventHub`. Simple, no new infra.
- Option B: **Poll a `job_events` append-only table** with a cursor. More robust for missed events but more DB load.
- Recommendation: start with LISTEN/NOTIFY; fall back to a small events table if we want resume-by-id semantics.

### 3.3 Heartbeating and graceful cancellation for any remaining long jobs

- Any handler that exceeds ~60s should call `repo.heartbeat(job_id)` every 10s (either explicitly or via a helper context manager).
- Handlers should check `asyncio.CancelledError` propagation and commit partial state before re-raising so deploys don't lose progress.
- Deprecate `JOB_EXECUTION_TIMEOUT_SEC=1800` as a common-case timeout; set per-kind timeouts in `JobService._get_handler`.

### 3.4 Right-size API and worker services

- After 3.1 and diagnostics are in place:
  - API: probably fine at `cpu=256, memory=1024` with `--workers 2 --threads 4` or similar.
  - Worker: `cpu=512, memory=2048` with `--workers 1`, runs the async worker loop + thread pool.
- Concrete numbers come from Category 1 data, not guesses.

### 3.5 Progressive SSE/polling migration on the frontend — COURSE HANDOFF DONE

- SSE removed from all single-job flows. `job-events-hub.ts` is gone; SSE kept only for the admin jobs dashboard (`/api/v1/jobs/stream`).
- `createJobTracker` (explicit local tracking) and `createJobPolling` (single known-job reactive primitive) cover all non-admin flows. `waitForJobResult` for promise-style generation flows.
- §3.6 child-chaining closes the most critical "job spawns children" gaps (lecture generation, image generation) without broad polling.
- New Course Creation now preserves same-tab SPA continuity from `Courses.tsx` to `CourseDetail.tsx`: the client registers a course-scoped handoff before navigation, the detail page adopts it, discovers active child jobs, and refreshes the course image/topics when jobs complete.

**Completed — limited SPA navigation handoff for New Course Creation:**

The polling primitives are intentionally page-local. That is fine while the user
stays put, but it loses continuity when the initiating page navigates away. The
important case is New Course Creation:

1. `Courses.tsx` enqueues `create_course` and polls that known job.
2. The backend creates the course, then enqueues follow-up jobs for the new
   course (`generate_course_image`, `generate_topics_for_course`, and any topic
   slot children).
3. `Courses.tsx` receives the completed `create_course` job and navigates to
   `/courses/{course_id}`.
4. The `Courses.tsx` polling primitive is cleaned up on unmount, so
   `CourseDetail.tsx` has no in-memory awareness of the parent or follow-up jobs.
   Backend work succeeds, but the detail page does not refresh image/topics.

Implemented with a session-scoped handoff registry + page adoption.

Keep the scope deliberately narrow: continuity across same-tab SPA navigation,
not hard refresh, cross-tab, or multi-device sync.

- Added a module-level registry in `web/src/utils/job-management.ts`:
  `Map<string, JobHandoff>`, cleared naturally on hard refresh and pruned on TTL
  or terminal state. Use entity-scoped keys like `course:{courseId}` rather than
  only `job:{jobId}` so the destination route can adopt without knowing every
  child ID up front.
- When `Courses.tsx` sees `create_course` complete, it parses:
  - `course_id` from `job.result.course_id`
  - `topics_job_id` from `job.result.topics_job_id` when present
  - the parent `create_course` job ID from `job.id`
- Before calling `navigate('/courses/{id}')`, it registers a handoff:
  ```ts
  registerJobHandoff({
    entity: { type: 'course', id: courseId },
    parentJobIds: [createCourseJobId],
    jobIds: [topicsJobId].filter(Boolean),
    kinds: [
      'create_course',
      'generate_course_image',
      'generate_topics_for_course',
      'generate_topic_for_course_slot',
    ],
    expiresAt: Date.now() + 10 * 60_000,
  })
  ```
- On `CourseDetail.tsx` mount, the page calls an adoption helper for the current course:
  `adoptJobHandoff({ entity: { type: 'course', id: courseId }, ...callbacks })`.
  The helper:
  - track known `jobIds`
  - query `GET /jobs/{parent}/children` once for each known parent and track
    active direct children
  - with `trackChildren: true`, continue discovering any slot-child chain as
    each parent/sibling completes
  - prunes handoffs by TTL; follow-up work can remove handoffs eagerly once
    there are no active jobs left
- In `CourseDetail.tsx`, completion callbacks refresh only affected
  resources:
  - `generate_course_image` done → `refetchCourse()`
  - `generate_topics_for_course` done → `refetchTopics()`
  - `generate_topic_for_course_slot` done → `refetchTopics()` (or throttle/debounce
    to avoid one request per slot if topics are generated in a fast burst)
  - `create_course` done can be ignored on the detail page except for child
    discovery, because the course page is already loaded.

**Scoped fallback when registry has no record — implemented:**

Use this only on the destination page and only for likely-stale placeholders
(e.g., course has no image or topics are empty). It should run for a short window
after mount, then stop.

- Query active jobs for the course, not all user jobs:
  - `GET /jobs?course_id={courseId}&status=queued`
  - `GET /jobs?course_id={courseId}&status=running`
- Filter to relevant kinds:
  `generate_course_image`, `generate_topics_for_course`,
  `generate_topic_for_course_slot`.
- Track any returned IDs with the same `createJobTracker` path and
  `trackChildren: true`.
- This recovers from small race windows, direct deep links after course creation
  in the same tab, or a missing `topics_job_id`, without broad eager polling.

**Backend contract verified for course creation:**

- `create_course` result includes `course_id` and includes
  `topics_job_id` when topic generation is enqueued.
- `generate_course_image`, `generate_topics_for_course`, and
  `generate_topic_for_course_slot` payloads include `course_id`, so
  `GET /jobs?course_id={id}` can recover active work.
- Child topic-slot jobs are discoverable through the active course/job filters
  used by the handoff adoption path.

**Non-goals for this phase:**

- No always-on polling in `CourseDetail.tsx`.
- No cross-tab or hard-refresh recovery beyond the scoped fallback above.
- No return to SSE for course detail pages.

**Still to do: identify other SPA handoff cases.**

- Audit the web client for other flows where a component starts a known job and
  then navigates before downstream jobs complete.
- For each confirmed case, either wire it into `registerJobHandoff` /
  `adoptJobHandoff` with an entity-scoped key or explicitly document why local
  tracking is sufficient.
- Likely candidates to review: quickstart finalization → course detail,
  topic-to-lecture creation flows, and any admin/detail transitions that enqueue
  jobs before route changes.

### 3.6 Standardize follow-up chaining — DONE (2026-04-29)

**Approach chosen:** `parent_job_id` column on the jobs table (nullable FK, self-referential). Preferred over threading child IDs through return values because it decouples the tracking concern from service return signatures and makes the tree queryable at any time.

**Backend (2026-04-29):**

- **Migration** (`alembic/versions/d7e8f9a0b1c2`): added `parent_job_id INTEGER REFERENCES jobs(id)` + `idx_jobs_parent_job_id`.
- **`JobModel`** (`artificial_u/models/database.py`): added `parent_job_id` column.
- **`JobRepository.create()`** (`artificial_u/models/repositories/job.py`): added `parent_job_id` param; `list()` now filters by `parent_id`.
- **`JobEnqueueService`** (`artificial_u/services/job_enqueue_service.py`): all `enqueue_*` methods now return `int` (job ID, or `None` in test mode) and accept `parent_job_id` keyword arg.
- **`CourseService.create_course()` / `_save_course()`** (`artificial_u/services/course_service.py`): threads `parent_job_id` through so the course image job gets parented correctly even though it's enqueued inside the domain service.
- **`LectureGeneratorService`** (`artificial_u/services/lecture_generator_service.py`): `generate_and_save_lecture` and `generate_lecture_audio` both accept `parent_job_id` and pass it through to `_enqueue_background_jobs_for_lecture` → summary/audio/timeline enqueue calls. Without this, `generate_lecture` children were unparented and invisible to the frontend.
- **`JobService.dispatch()`** (`artificial_u/services/job_service.py`): added `parent_job_id` param, passes it to every handler. All handlers updated with `parent_job_id=None` kwarg; handlers that enqueue children pass it through. `_handle_create_course` now returns `topics_job_id` in its result. Slide chain: `_build_lecture_slide_chain` embeds `chain_parent_job_id` in each payload; `_enqueue_next_lecture_slide` reads it and sets `parent_job_id` on next-slide rows, so all slides point to the `generate_lecture_images` job.
- **Worker** (`artificial_u/api/worker.py`): `_execute_job` passes `parent_job_id=job_id` to `dispatch()`, so every job's children are automatically linked.
- **Jobs router** (`artificial_u/api/routers/jobs.py`): `parent_job_id` exposed in all job response shapes; `GET /jobs?parent_id={id}` supported; new `GET /jobs/{id}/children` endpoint returns direct children.

**Frontend (2026-04-29):**

- **`jobs-service.ts`**: `JobRow` gains `parent_job_id?: number | null`; `listJobChildren(parentJobId)` function added; `listJobs` accepts `parent_id` param.
- **`job-management.ts`** — `createJobTracker` gains `trackChildren?: boolean` option. When a tracked job completes, `trackJobChildren` fires (fire-and-forget):
  1. Fetches `/jobs/{id}/children` — auto-tracks any non-terminal direct children.
  2. If the completing job has a `parent_job_id`, also fetches `/jobs/{parent}/children` to find non-terminal *siblings* — this is what drives the slide chain, where each slide enqueues the next as a sibling (same parent), not a child.
- **Entity-navigation guard**: the `createEffect` that calls `stop()` on entity ID changes was previously firing when `lectureId` transitioned from `undefined` to a real ID (new lecture just created) or when the `lecture()` prop briefly refreshed after a job completed. Fixed to only stop when an existing defined ID changes to a *different* defined ID — i.e., genuine SPA navigation, not data arrival.
- **`TopicDetail.tsx`**: added `generate_lecture_timeline` to the `kinds` list (it was filtered out, breaking the audio → timeline chain); added `generate_lecture_timeline` to `onJobComplete` so `refetchLecture()` fires when the timeline finishes (gates the "Generate Lecture Images" button).
- **`trackChildren: true`** wired into `TopicDetail`, `LectureDetail`, and `LectureSection` trackers.

**Verified job trees (live testing):**
```
generate_lecture (id=N)                      ← tracked by TopicDetail
  ├── generate_lecture_summary (parent=N)    ← auto-tracked as child
  └── generate_lecture_audio   (parent=N)    ← auto-tracked as child
        └── generate_lecture_timeline        ← auto-tracked as child of audio

generate_lecture_images (id=M)              ← tracked by LectureSection
  ├── generate_lecture_slide slot 0 (parent=M)   ← auto-tracked as child
  ├── generate_lecture_slide slot 1 (parent=M)   ← auto-tracked as sibling
  ├── ...
  └── generate_lecture_slide slot N-1 (parent=M) ← auto-tracked as sibling
```
Frontend follows the full tree to completion; UI updates (audio player, timeline gate, image gallery) appear without manual refresh.

**Still to do / open decisions:**
- Remove the `[job-chain]` debug `console.log` statements from `job-management.ts` once behavior is confirmed stable in production.
- Wire `trackChildren: true` into the course creation page / quickstart flow (SPA navigation gap means the tracker is often gone by the time children are enqueued — see §3.5).
- `generate_topics_for_course` enqueues individual lecture jobs inside `topic_generator_service`; those could be parented to the topics job if the service accepts `parent_job_id`. Deferred — requires threading into the generator service layer.
- Workflow library abstraction (`arq` groups etc.) — still not worth it until branching logic accretes.

---

## Category 4 — Long-term / larger architectural moves

Bigger investments that should wait until metrics or workload demand them. Listed
so we know where we're heading and why.

### 4.1 Autoscaling on queue depth

- Once worker is separate and `jobs.queued` is a published metric, add an ECS target-tracking scaling policy on a derived `queued_per_running_worker` metric.
- Don't autoscale the API on CPU until we have evidence; most of your traffic is cached via CloudFront.

### 4.2 Async SQLAlchemy (asyncpg)

- Remove the `asyncio.to_thread` contortions currently wrapping sync repo calls.
- Worth it when either (a) you've actually profiled thread contention as a bottleneck, or (b) you're adding significantly more DB-heavy async endpoints.
- Migration cost is non-trivial across all repositories. Not a priority.

### 4.3 Consider a real queue library if/when Postgres hits a wall

- Candidates in ascending order of footprint: `arq` (Redis, Python-native, small), `taskiq` (async-first), `rq`, `celery`.
- Trigger conditions: queue depth of hundreds, need for delayed scheduling beyond `run_after`, multi-region workers, wanting a mature UI and stats out of the box.
- We are nowhere near this today.

### 4.4 Direct client → S3 uploads for large binary flows

- For future consumer-uploaded content (audio, images), skip the server's memory entirely via presigned PUT URLs.
- Not a current pain point since users don't upload.

### 4.5 Re-evaluate choice of cloud provider / managed options

- Long-range: once we have solid metrics on compute vs storage vs egress costs, evaluate whether Vercel + Neon + S3, or a simple Hetzner/Fly box, would reduce ops cost for the workload shape.
- Explicitly out of scope for this plan.

---

## Category 5 — Open questions / to revisit

Things where we don't have enough information yet or where the right answer
depends on outcomes above.

### 5.1 Is memory actually leaking, or just steady-state heavy?

- **2026-04-28 prod data (memory-drift telemetry + OOM log):** Confirmed pattern is **spiky per-job allocation + glibc malloc retention**, not a monotonic leak. Workers hit 1.0–1.3 GB RSS during `generate_lecture_timeline` jobs (MP3 bytes twice in heap), then stay there even at inflight=0. Two workers × ~1 GB = OOM at 97% on a 2 GiB task.
- **Root cause addressed:** §2.8 (gunicorn workers 2→1) removes the double-worker pressure immediately. §2.10 (streaming MP3 to temp file) removes the primary heap spike on timeline jobs.
- **Post-§2.10 observation:** After MP3 streaming landed, RSS stabilised at ~70% (~1.4 GB on a 2 GiB task) with no OOM kills. Confirmed as glibc arena retention, not a leak — memory was logically free but not returned to the OS.
- **§2.13 response:** `MALLOC_ARENA_MAX=2` + `malloc_trim(0)` post-job address the retention directly. Expected steady-state to drop to ~50–60% (≈1.0–1.2 GB); watch 24h prod data post-deploy.
- If RSS is still above 70% after §2.13 lands, audit remaining `download_file` callers and use `DIAG_TRACEMALLOC=1` on-demand.
- **Initial finding (dev, idle vs single lecture run):** the biggest *new* allocation was the audio object being read fully into memory (`storage_service.py:349`, ≈24 MB). Prod data confirmed and amplified this.

### 5.2 Do we need per-user cross-tab live state for any flow?

- Today: no. Single-owner model + polling on the foreground tab is acceptable.
- Revisit if we see actual confusion or clobbering reports from users.
- If revisited, the cheapest implementation is: poll `/jobs?created_by=me&status=running,queued` on every tab; tab state is reactive.

### 5.3 Admin + owner simultaneous editing

- Accepted edge case. Revisit only if it becomes a real support issue.

### 5.4 Should we surface provider-level rate limits instead of a single global RPS?

- `OUTBOUND_RPS=1` is extremely conservative. With image batch splitting + per-provider pools, we might want per-provider limiters (`gemini_limiter`, `elevenlabs_limiter`, `openai_limiter`). Depends on how often 429s show up in logs after 2.2/2.3 land.

### 5.5 Progress UX for split batches

- If lecture-image generation becomes 30 tiny jobs, the "user waits" UX becomes a progress bar over `done / total` slides.
- Where does that progress state live? Options: (a) compute on demand by counting jobs with `payload.batch_id`; (b) store per-batch progress in the timeline JSON in S3 (already partially done); (c) new `job_batches` table.
- Pick when 2.2 is designed.

### 5.6 SSE for the admin dashboard — worth keeping at all?

- If 2.5 goes well and the admin dashboard is used rarely, we might scrap SSE entirely and poll there too (e.g., every 2s with filtering). Defer decision until after 3.2 is scoped; if LISTEN/NOTIFY is cheap, SSE stays.

---

## Suggested sequencing (concrete)

1. **Week 0–1 (diagnostics):** land 1.1, 1.2, 1.3 behind env flags. Start building a baseline memory/job dashboard in CloudWatch.
2. **Week 1–2 (quick wins):** 2.1 (visibility timeout), 2.3 (slot idempotency), 2.4 (SSE hygiene), 2.6 (httpx reuse), 2.10 (stream large media), 2.11 (reuse boto3 clients), 2.12 (reduce JSON churn), 2.8 (gunicorn tuning). All small.
3. **Week 2–3 (splitting + polling):** 2.2 (split lecture images) + 2.5 (swap user-waiting flows to polling) + 2.7 (priority lanes). This is the highest-impact batch.
4. **Week 3+ (structural):** 3.1 (worker service in CDK), 2.9 (stopTimeout), 3.2 (LISTEN/NOTIFY for admin dashboard), 3.3 (heartbeating helper).
5. **After data comes in:** 3.4 (right-sizing), 3.5 (frontend migration cleanup), 3.6 (workflow standardization).
6. **Wait-and-see:** Category 4.

---

## Non-goals (explicit)

- Cross-tab / multi-device live job state.
- Horizontal autoscaling on CPU.
- Redis, Celery, or any new infra dependency.
- Moving away from SSE entirely before we've tried scoping it to the admin dashboard.
- Async SQLAlchemy migration.
