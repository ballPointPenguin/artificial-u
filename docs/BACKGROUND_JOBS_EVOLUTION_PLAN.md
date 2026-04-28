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

### 2.5 Swap user-waits-for-result flows from SSE → polling

- For "user clicks generate, sees progress, waits for done" UX on a single job, switch to polling `GET /jobs/{id}` every 2s while status is `queued`/`running`, stop on terminal state.
- Keep SSE subscription only for admin dashboards (`/api/v1/jobs/stream`).
- Remove SSE use from single-job pages to simplify client code and remove cross-worker event-loss.
- Frontend: `web/src/utils/job-events-hub.ts` gets a sibling `useJobPolling(jobId)` hook; migrate call sites incrementally.

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

### 2.8 Tune Gunicorn for I/O-bound workload

- Current: `--workers 2 --threads 8` on 1 vCPU / 2 GiB. Over-subscribed given most work is I/O.
- Try: `--workers 2 --threads 4` or `--workers 1 --threads 16` and compare memory and latency via Category 1 metrics.
- Parameter sweep is safe because changes are revert-in-one-deploy.

### 2.9 Raise ECS `stopTimeout` to give workers a chance to finish

- In the CDK Fargate service, set `stopTimeout` to 120s (the max is 120s on Fargate) so the worker has real time to stop jobs gracefully on deploy.
- Update `Worker.stop()` to wait up to N seconds for in-flight `_run_one` tasks to complete before cancelling.
- Pairs with 2.2: short jobs finish in seconds, so graceful shutdown Just Works.

### 2.10 Stream large media in `StorageService` (don't hold full files in memory)

Confirmed by `tracemalloc` load-trace (single lecture run): the largest live allocation was ~24 MB at:

- `artificial_u/services/storage_service.py:349` → `return file_obj.read(), content_type` (≈24 MB, count_diff=1)

Local sizes during that run: lecture MP3 22.8 MiB, timeline JSON 464 KiB, lecture text 21.1 KiB. The MP3 explains the spike: the storage layer reads the entire object into memory.

Actions:

- Audit all read paths in `StorageService` that use `body.read()` / `file_obj.read()` and convert to streaming where the consumer does not need the full bytes.
  - For S3/MinIO downloads: stream the response body in chunks (e.g., iterate `body.iter_chunks(...)`) directly into the next consumer (HTTP response, ffmpeg stdin, hash, length probe).
  - For uploads: prefer `upload_fileobj` / multipart over loading bytes into a `bytes` buffer.
- Avoid round-tripping audio bytes through Python just to compute metadata. Use HEAD/`get_object_attributes` for size/content-type and only `range`-fetch the bytes you need (e.g., first/last KBs for ID3, `ffprobe` over a streamed range).
- For ffmpeg integration, prefer piping (`stdin`/`stdout`) or local temp files over loading the full MP3 into RAM.

Expected impact:

- Eliminates the dominant memory spike on the audio pipeline; flattens RSS during long lecture jobs.
- Reduces peak GC pressure and makes Category 5.1 easier to answer with real data.

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

### 3.5 Progressive SSE/polling migration on the frontend

- Finish the client-side migration from SSE to polling for all non-admin flows.
- Remove `job-events-hub.ts` from single-page flows; keep for the admin dashboard.
- Document in `web/STYLE_GUIDE.md` (or a job-handling guide) which pattern to pick for new features.

### 3.6 Standardize follow-up chaining

- The follow-up chain in `artificial_u/api/worker.py:_handle_follow_up` is powerful but bespoke. Consider replacing with a small "workflow" abstraction:
  - Each workflow row has an ordered list of steps; worker enqueues the next step on completion.
  - Or adopt an existing library (`arq` groups, `taskiq` workflows) if we decide to switch queues.
- Only worth doing if follow-up semantics start accreting more branching logic.

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

- Answered by 1.1 + 1.5. If RSS climbs monotonically over days, track down; if it plateaus at 1.2 GiB, it's just Python + imports + thread pool + connection pools, and the answer is right-sizing (3.4), not leak-hunting.
- **Initial finding (dev, idle vs single lecture run):** the biggest *new* allocation was the audio object being read fully into memory (`storage_service.py:349`, ≈24 MB). That matches the MinIO file sizes observed (MP3 22.8 MiB; timeline JSON 464 KiB; lecture text 21.1 KiB) and points to “spiky per-job allocations” more than a classic leak. Prioritize 2.10–2.12, then re-check 1.1/1.5 over a 24h prod window.

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
