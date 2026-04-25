# Jobs Scaffold for ArtificialU (FastAPI + Postgres + SQLAlchemy + SolidJS)

A compact, single‑host job system using only Postgres + a FastAPI in‑process worker. Includes:

* SQL schema
* FastAPI app with: enqueue API, job reservation with `FOR UPDATE SKIP LOCKED`, async worker, throttling, retries, sweeper, and a tiny admin summary endpoint
* SolidJS component to display job status with simple polling

> This is a starting point. Adjust names, error handling, and auth per your app.

---

## ArtificialU-specific assessment and plan

This section adapts the sketch to this repository’s current architecture. Keep the reference scaffold below for inspiration; follow this plan for implementation in ArtificialU.

> **Production note (Dec 2025):** All long-running AI endpoints that sit behind
> CloudFront/ALB—including professor generation—should now enqueue jobs via
> `/api/v1/.../enqueue` and rely on the worker + jobs UI. The synchronous
> `/professors/generate` route exists mainly for local/dev usage where CDN
> timeouts are not a factor.

### Current asyncio usage in this codebase

* In `artificial_u/services/lecture_service.py`, summaries are scheduled via `asyncio.get_running_loop().create_task(...)` with a thread fallback. This decouples summary generation from the request that created/updated a lecture.
* In `artificial_u/services/professor_service.py`, professor image generation is scheduled similarly as a background task.
* Content generation and image generation services (`artificial_u/services/content_service.py`, `artificial_u/services/image_service.py`) are fully async and already include retry/backoff. They currently run within request handlers for endpoints like `POST /api/v1/lectures/generate`, which means the client waits for completion.
* DB access is synchronous SQLAlchemy (see `artificial_u/models/repositories/*` and `BaseRepository`). This can block the event loop if called directly from async contexts.
* There is no centralized job table/queue; background work is ephemeral tasks started from services.

Implication: for long-running AI calls, we should enqueue a job and return immediately. A single-process worker loop can safely run in the same FastAPI app, using Postgres row locking for concurrent safety. To avoid starving the event loop, wrap blocking DB calls in `asyncio.to_thread` when invoked from async job runners.

References: rate limiting with a leaky bucket (`aiolimiter.AsyncLimiter`) and asyncio primitives: see `https://aiolimiter.readthedocs.io/en/stable/` and `https://docs.python.org/3/library/asyncio.html`.

### Target design for ArtificialU

* Storage: Postgres table `jobs` managed via Alembic + SQLAlchemy model in `artificial_u/models/database.py`.
* Access layer: `JobRepository` in `artificial_u/models/repositories/job.py` exposing: `create`, `get`, `list`, `reserve_one(skip_locked)`, `mark_done`, `mark_failed_or_retry(run_after)`, `sweep_stuck`.
* API layer: new FastAPI router `artificial_u/api/routers/jobs.py` with endpoints:
  * `POST /api/v1/jobs` → enqueue and return job row
  * `GET /api/v1/jobs/{id}` → fetch job
  * `GET /api/v1/jobs` → list/filter
  * `GET /api/v1/jobs/summary` → counts by status
* Worker: an in-process async loop started at application startup (via lifespan or startup event in `artificial_u/api/app.py`):
  * Uses `SELECT … FOR UPDATE SKIP LOCKED` (via SQLAlchemy) to reserve a job
  * Runs jobs with local concurrency cap using `asyncio.Semaphore`
  * Applies per-process rate limiting to outbound provider calls with `aiolimiter.AsyncLimiter`
  * Retries with exponential backoff by setting `run_after` and returning job to `queued`
  * Sweeps stuck `running` jobs whose `updated_at` is older than a visibility timeout
* Handlers (initial kinds):
  * `generate_lecture_summary` → `LectureService.generate_lecture_summary(lecture_id)` (async)
  * `generate_professor_image` → `ProfessorService.generate_and_set_professor_image(professor_id, aspect_ratio)` (async)
  * Optional: `generate_lecture` → `LectureService.generate_lecture(partial_attributes)`; decide whether to persist within handler or return result into `jobs.result`
* Frontend: add a minimal SolidJS component to poll job status and render results; no websockets required initially.

### Schema (Alembic + SQLAlchemy)

Add a `JobModel` to `artificial_u/models/database.py` and an Alembic migration to create the `jobs` table:

```sql
-- columns
id            BIGSERIAL PRIMARY KEY,
kind          TEXT NOT NULL,
payload       JSONB NOT NULL,
status        TEXT NOT NULL DEFAULT 'queued',  -- queued | running | done | failed | cancelled
priority      INT  NOT NULL DEFAULT 0,
run_after     TIMESTAMPTZ NOT NULL DEFAULT now(),
attempts      INT  NOT NULL DEFAULT 0,
max_attempts  INT  NOT NULL DEFAULT 5,
last_error    TEXT,
result        JSONB,
created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()

-- helpful indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status_priority_runafter
  ON jobs (status, priority DESC, run_after);
CREATE INDEX IF NOT EXISTS idx_jobs_status_updatedat ON jobs (status, updated_at);
```

Use SQLAlchemy’s `with_for_update(skip_locked=True)` (or Core `select(...).with_for_update(skip_locked=True)`) in the repository to implement reservation.

### Worker loop integration

* Initialize shared state at API startup (in `artificial_u/api/app.py`):
  * `app.state.limiter = AsyncLimiter(max_rate=settings.OUTBOUND_RPS, time_period=1)`
  * `app.state.job_semaphore = asyncio.Semaphore(settings.WORKER_MAX_CONCURRENCY)`
  * Spawn a long-running `asyncio.create_task(worker_loop(app.state))`
* In the worker loop:
  * Periodically call `sweep_stuck_jobs()`
  * Try up to `WORKER_MAX_CONCURRENCY` reservations per tick; wrap each job in `asyncio.create_task(run_one(row)))`
  * In `run_one`, do:
    * `async with limiter:` around the part that calls external providers
    * `await asyncio.wait_for(handler(payload), timeout=JOB_TIMEOUT_SEC)`
    * Mark done or retry/fail based on outcome; compute backoff with jitter
* Note: create the limiter once per event loop (don’t share across loops), per `aiolimiter` docs.

### Repository considerations

* DB access is synchronous; when called from async worker code, use `await asyncio.to_thread(repo_method, ...)` for heavier operations (queries that might block) to keep the event loop responsive.
* Keep transaction scopes tight and update `updated_at` on each state transition.

### Rate limiting and backoff

* Use `aiolimiter.AsyncLimiter` for global outbound RPS. For variable “weight” calls, use `await limiter.acquire(n)` where appropriate. See `https://aiolimiter.readthedocs.io/en/stable/`.
* Exponential backoff with jitter on retries; store schedule in `run_after` for requeueing.

### Generate actions to migrate to jobs

Each of these should be enqueued via `POST /api/v1/jobs` (or specific “enqueue” endpoints) and processed by the worker with dedicated handlers:

* generate image → kind: `generate_professor_image`, payload: `{ "professor_id": number, "aspect_ratio"?: string }`
* generate department → kind: `generate_department`, payload: `{ "partial_attributes"?: dict, "freeform_prompt"?: string }`
* generate course → kind: `generate_course`, payload: `{ "partial_attributes"?: dict, "freeform_prompt"?: string }`
* generate professor → kind: `generate_professor`, payload: `{ "partial_attributes"?: dict, "freeform_prompt"?: string }`
* generate topics → kind: `generate_topics_for_course`, payload: `{ "course_id": number, "freeform_prompt"?: string }`
  * Handler behavior: generate canonical topic slots sequentially by `(week, order)`, one topic at a time, so each prompt sees the full prior course progression.
* generate lecture → kind: `generate_lecture`, payload: `{ "partial_attributes": { "course_id": number, "topic_id": number, ... }, "freeform_prompt"?: string }`
* generate lecture summary → kind: `generate_lecture_summary`, payload: `{ "lecture_id": number }`
* generate lecture audio → kind: `generate_lecture_audio`, payload: `{ "lecture_id": number }`
* quickstart start → kind: `quickstart_start`, payload: `{ "query": string, "created_by": number }` — generates course from user query with smart department/professor selection; returns course_id, professor_id, department_id, etc.

Results can be stored in `jobs.result` (e.g., summary text, created entity IDs/URLs), and/or persisted by the handler as appropriate.

---

## Minimal file tree (suggested)

```txt
backend/
  app.py
  settings.py
  db.py
  job_handlers.py
  requirements.txt  # or pyproject.toml
migrations/
  0001_jobs.sql
web/
  src/components/JobStatus.tsx
```

---

## 1) SQL schema (Postgres)

**`migrations/0001_jobs.sql`**

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- optional if you want gen_random_uuid()

CREATE TABLE IF NOT EXISTS jobs (
  id            BIGSERIAL PRIMARY KEY,
  kind          TEXT NOT NULL,                      -- e.g., 'summarize', 'render', etc.
  payload       JSONB NOT NULL,                     -- parameters for the job
  status        TEXT NOT NULL DEFAULT 'queued',     -- queued | running | done | failed | cancelled
  priority      INT  NOT NULL DEFAULT 0,
  run_after     TIMESTAMPTZ NOT NULL DEFAULT now(),
  attempts      INT  NOT NULL DEFAULT 0,
  max_attempts  INT  NOT NULL DEFAULT 5,
  last_error    TEXT,
  result        JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status_priority_runafter
  ON jobs (status, priority DESC, run_after);

-- Useful if you implement a sweeper for stuck jobs:
CREATE INDEX IF NOT EXISTS idx_jobs_status_updatedat ON jobs (status, updated_at);
```

---

## 2) Python backend (FastAPI)

### 2.1 Dependencies

**`backend/requirements.txt`** (pin as you like)

```txt
fastapi
uvicorn[standard]
asyncpg
pydantic
pydantic-settings
aiolimiter
python-dotenv
```

> You can swap to SQLAlchemy async if you prefer; `asyncpg` keeps this minimal.

### 2.2 Settings

**`backend/settings.py`**

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., description="Postgres URL, e.g. postgresql://user:pass@localhost:5432/db")

    # worker tuning
    WORKER_POLL_IDLE_SEC: float = 0.75        # sleep when no job reserved
    WORKER_VISIBILITY_TIMEOUT_SEC: int = 2100 # consider running jobs stuck after this
    WORKER_MAX_CONCURRENCY: int = 3           # local concurrency for job execution

    # rate limiting to external providers (simple global token bucket)
    OUTBOUND_RPS: int = 1
    OUTBOUND_BURST: int = 1

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2.3 DB helper

**`backend/db.py`**

```python
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

async def init_pool(dsn: str):
    global _pool
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)

async def pool() -> asyncpg.Pool:
    assert _pool is not None, "Pool not initialized"
    return _pool

async def fetchrow(query: str, *args):
    p = await pool()
    async with p.acquire() as conn:
        return await conn.fetchrow(query, *args)

async def fetch(query: str, *args):
    p = await pool()
    async with p.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute(query: str, *args):
    p = await pool()
    async with p.acquire() as conn:
        return await conn.execute(query, *args)
```

### 2.4 Job handlers

**`backend/job_handlers.py`**

```python
import asyncio
from typing import Any, Dict
from aiolimiter import AsyncLimiter

# In a real app, inject this limiter from settings/app state
outbound_limiter = AsyncLimiter(1, 1)  # default, overridden by app.py

class JobError(Exception):
    pass

async def fake_ai_call(prompt: str) -> str:
    # Simulate a slow third‑party AI request with rate‑limit guard
    async with outbound_limiter:
        await asyncio.sleep(1.5)  # replace with real HTTP call
    return f"AI result for: {prompt[:48]}…"

async def handle_summarize(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload.get("text")
    if not text:
        raise JobError("Missing 'text' in payload")
    result = await fake_ai_call(text)
    return {"summary": result}

HANDLERS = {
    "summarize": handle_summarize,
}

async def dispatch_job(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    handler = HANDLERS.get(kind)
    if not handler:
        raise JobError(f"No handler for kind={kind}")
    return await handler(payload)
```

### 2.5 FastAPI app with worker

**`backend/app.py`**

```python
import asyncio
import datetime as dt
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from settings import settings
from db import init_pool, pool, fetchrow, fetch, execute
from job_handlers import dispatch_job, outbound_limiter

app = FastAPI()

# ---- Models ----
class EnqueueJob(BaseModel):
    kind: str
    payload: Dict[str, Any]
    priority: int = 0
    run_after: Optional[dt.datetime] = None
    max_attempts: int = 5

# ---- Helpers ----

def backoff_seconds(attempts: int) -> float:
    # exponential backoff with jitter
    base = min(2 ** attempts, 60)  # cap growth
    jitter = 0.25 * base
    return base + (jitter * (0.5 - __import__("random").random()))

async def reserve_one_job():
    q = """
    WITH cte AS (
      SELECT id
      FROM jobs
      WHERE status = 'queued' AND run_after <= now()
      ORDER BY priority DESC, id
      FOR UPDATE SKIP LOCKED
      LIMIT 1
    )
    UPDATE jobs j
    SET status = 'running', updated_at = now(), attempts = attempts + 1
    FROM cte
    WHERE j.id = cte.id
    RETURNING j.*;
    """
    return await fetchrow(q)

async def mark_done(job_id: int, result: Dict[str, Any]):
    await execute(
        """
        UPDATE jobs
        SET status='done', result=$2, updated_at=now()
        WHERE id=$1
        """,
        job_id, result,
    )

async def mark_failed(job_id: int, attempts: int, max_attempts: int, error: str):
    if attempts >= max_attempts:
        await execute(
            """
            UPDATE jobs
            SET status='failed', last_error=$2, updated_at=now()
            WHERE id=$1
            """,
            job_id, error[:2000]
        )
    else:
        delay = backoff_seconds(attempts)
        await execute(
            """
            UPDATE jobs
            SET status='queued', last_error=$2, run_after=now() + make_interval(secs => $3), updated_at=now()
            WHERE id=$1
            """,
            job_id, error[:2000], delay,
        )

async def sweep_stuck_jobs():
    # Requeue jobs that have been 'running' for too long (process crashed?)
    timeout = settings.WORKER_VISIBILITY_TIMEOUT_SEC
    await execute(
        """
        UPDATE jobs
        SET status='queued', updated_at=now()
        WHERE status='running' AND updated_at < now() - make_interval(secs => $1)
        """,
        timeout,
    )

async def worker_loop():
    # set up global limiter from settings
    outbound_limiter.rate = settings.OUTBOUND_RPS
    outbound_limiter.time_period = 1
    # local concurrency gate
    sem = asyncio.Semaphore(settings.WORKER_MAX_CONCURRENCY)

    async def run_one(job_row):
        async with sem:
            job_id = job_row["id"]
            kind = job_row["kind"]
            payload = job_row["payload"]
            attempts = job_row["attempts"]
            max_attempts = job_row["max_attempts"]
            try:
                # optional per-job timeout
                result = await asyncio.wait_for(dispatch_job(kind, payload), timeout=300)
                await mark_done(job_id, result)
            except Exception as e:  # broad catch to mark failed
                await mark_failed(job_id, attempts, max_attempts, str(e))

    # main loop
    while True:
        try:
            # sweep occasionally
            await sweep_stuck_jobs()

            # try to reserve several jobs up to concurrency
            tasks = []
            for _ in range(settings.WORKER_MAX_CONCURRENCY):
                row = await reserve_one_job()
                if not row:
                    break
                tasks.append(asyncio.create_task(run_one(row)))

            if tasks:
                await asyncio.gather(*tasks)
            else:
                await asyncio.sleep(settings.WORKER_POLL_IDLE_SEC)
        except Exception:
            # Don't let the loop die; back off briefly on unexpected errors
            await asyncio.sleep(2.0)

# ---- API routes ----

@app.on_event("startup")
async def on_startup():
    await init_pool(settings.DATABASE_URL)
    asyncio.create_task(worker_loop())

@app.post("/jobs")
async def enqueue(job: EnqueueJob):
    run_after = job.run_after or dt.datetime.utcnow()
    row = await fetchrow(
        """
        INSERT INTO jobs (kind, payload, status, priority, run_after, max_attempts)
        VALUES ($1, $2, 'queued', $3, $4, $5)
        RETURNING *
        """,
        job.kind, job.payload, job.priority, run_after, job.max_attempts,
    )
    return dict(row)

@app.get("/jobs/{job_id}")
async def get_job(job_id: int):
    row = await fetchrow("SELECT * FROM jobs WHERE id=$1", job_id)
    if not row:
        raise HTTPException(404, "job not found")
    return dict(row)

@app.get("/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    if status:
        rows = await fetch(
            "SELECT * FROM jobs WHERE status=$1 ORDER BY created_at DESC LIMIT $2",
            status, limit,
        )
    else:
        rows = await fetch(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT $1", limit
        )
    return [dict(r) for r in rows]

@app.get("/jobs/summary")
async def jobs_summary():
    rows = await fetch(
        """
        SELECT status, count(*) AS n
        FROM jobs
        GROUP BY status
        ORDER BY status
        """
    )
    return {r["status"]: r["n"] for r in rows}
```

### Run it

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
uvicorn backend.app:app --reload
```

---

## 3) SolidJS: tiny job status component (polling)

**`web/src/components/JobStatus.tsx`**

```tsx
import { createSignal, onCleanup, onMount, Show } from "solid-js";

// Minimal polling client for /jobs/{id}
async function fetchJob(jobId: number) {
  const res = await fetch(`/api/jobs/${jobId}`); // proxy /api → FastAPI if needed
  if (!res.ok) throw new Error("failed to fetch job");
  return res.json();
}

interface JobStatusProps { jobId: number }

export default function JobStatus(props: JobStatusProps) {
  const [job, setJob] = createSignal<any>(null);
  const [err, setErr] = createSignal<string>("");

  let timer: number | undefined;

  const tick = async () => {
    try {
      const j = await fetchJob(props.jobId);
      setJob(j);
      setErr("");
      // stop polling once terminal
      if (["done", "failed", "cancelled"].includes(j.status)) {
        if (timer) clearInterval(timer);
      }
    } catch (e: any) {
      setErr(e.message || "error");
    }
  };

  onMount(() => {
    tick();
    timer = setInterval(tick, 2000) as unknown as number;
  });

  onCleanup(() => {
    if (timer) clearInterval(timer);
  });

  return (
    <div class="rounded-xl border p-3 text-sm">
      <Show when={job()} fallback={<span>Loading…</span>}>
        <div class="flex items-center justify-between">
          <div>
            <div class="font-semibold">Job #{job().id} · {job().kind}</div>
            <div class="opacity-70">Status: {job().status}</div>
            <div class="opacity-70">Attempts: {job().attempts} / {job().max_attempts}</div>
            <Show when={job().last_error}>
              <div class="text-red-700 mt-1 break-all">{job().last_error}</div>
            </Show>
          </div>
          <div class="text-right">
            <Show when={job().status === 'done'}>
              <pre class="text-xs bg-gray-50 p-2 rounded">{JSON.stringify(job().result, null, 2)}</pre>
            </Show>
          </div>
        </div>
      </Show>
      <Show when={err()}>
        <div class="text-red-700 mt-2">{err()}</div>
      </Show>
    </div>
  );
}
```

> For bulk displays, create a `JobsTable` that calls `/jobs?status=queued|running|failed|done` and renders a list with the same fields.

---

## Implementation steps (high level)

1) Dependencies and settings

* Add `aiolimiter` to project dependencies.

* Extend settings with:
  * `WORKER_POLL_IDLE_SEC`, `WORKER_VISIBILITY_TIMEOUT_SEC`, `WORKER_MAX_CONCURRENCY`
  * `OUTBOUND_RPS`

1) Schema

* Create Alembic migration to add `jobs` table and indexes.

* Add `JobModel` to `artificial_u/models/database.py`.

1) Repository and service layer

* Add `JobRepository` with methods for enqueue, reserve (skip locked), mark done/failed, sweep.

* Add `JobService` for dispatching to handlers and computing backoff with jitter.

1) Worker

* Add a worker module (e.g., `artificial_u/api/worker.py`) and start it from `artificial_u/api/app.py`
startup/lifespan. Keep references in `app.state` (limiter, semaphore, cancel handle).

* In `run_one`, wrap potentially blocking repo calls in `asyncio.to_thread`.

* Add handler wiring: implement a centralized job kind -> async handler map (eg generate_lecture_summary, etc) in the worker/service layer.

* Offload blocking IO in worker: wrap sync storage/boto3 calls and any sync repo operations with asyncio.to_thread (or switch to aioboto3).

* Graceful lifecycle: register shutdown to cancel the worker task(s) and wait for in-flight jobs to finish or requeue.

1) API

* Add `jobs` router with endpoints for enqueue, get, list, summary; include it in `create_application()`
with prefix `/api/v1`.

* For existing long-running routes (e.g., generate lecture/professor), consider adding alternate “enqueue”
versions that return a job id immediately.

1) Frontend

* Add the `JobStatus` component and simple flows to display job progress.

1) Tests

* Unit tests for `JobRepository` reservation semantics (including skip-locked) and backoff scheduling.

* Integration test for end-to-end: enqueue → worker processes → status becomes done → result present.

## Task checklist (initial)

* [x] Add `aiolimiter` to `pyproject.toml` dependencies.
* [x] Extend settings (API) with worker and rate-limit knobs; plumb into app state.
* [x] Create Alembic migration for `jobs` table and indexes.
* [x] Add `JobModel` (SQLAlchemy) in `artificial_u/models/database.py`.
* [x] Implement `JobRepository` in `artificial_u/models/repositories/job.py`.
* [x] Create `artificial_u/api/routers/jobs.py` and include it in `create_application()`.
* [x] Implement `artificial_u/api/worker.py` and start it on app startup.
* [x] Implement `JobService` (dispatch + backoff helper).
* [x] Add enqueue endpoints/flows for long-running operations (lecture summary/image/etc.).
* [x] Add SolidJS `JobStatus` component and integrate into UI where applicable.
* [ ] Add unit/integration tests for the job flow.

## Notes & tweaks

* **Throttling**: `aiolimiter` guards external calls. For simple concurrency caps, also adjust `WORKER_MAX_CONCURRENCY`.
* **Timeouts**: `asyncio.wait_for` per job; tune 300s as needed.
* **Cancellation**: add an endpoint to set `status='cancelled'` and make handlers check for cancellation.
* **Idempotency**: add a unique `idempotency_key` column; no‑op if result already exists.
* **Artifacts**: store large results elsewhere, keep a pointer/URL in `result`.
* **Security**: gate admin endpoints; don’t expose raw errors in prod.
* **SSE/WebSockets**: later, add a channel to push state changes; start with polling for simplicity.

### Debug notes and SSE implementation (2025-09)

#### SSE Connection Stability Issues and Resolution

**Problem**: SSE connections were closing every 1-4 seconds, causing constant reconnections and "stream" requests.

**Root Cause Discovery**:

1. Initial attempts to call `events.aclose()` on the async iterator failed (no such method)
2. The real issue: Using `asyncio.wait_for()` directly on `events.__anext__()` was **cancelling the async generator** when timeouts occurred
3. When an async generator is cancelled, it permanently breaks and raises `StopAsyncIteration` on all future calls

**Solution**: Redesigned event handling to avoid timeouts on the generator:

* Created a separate `event_reader()` task that consumes the hub's async generator without timeouts
* Main SSE loop uses `queue.get_nowait()` to check for events without blocking
* Continuous data flow with keepalives every 200ms ensures connection stability
* **Critical lesson**: Never use `asyncio.wait_for()` directly on async generator methods

**Best Practices Applied**:

* SSE requires continuous data flow - even comments (`:`) keep connections alive
* Send initial "connected" event to establish the stream
* Use heartbeat/ping events for connection health
* Clean up reader tasks properly in finally blocks

#### Job Payload Normalization

* Generate_lecture jobs use `{ "partial_attributes": { "topic_id": N, "course_id": M } }` format
* Audio/summary generation now includes both `lecture_id` and `topic_id` at top level for consistent filtering
* Repository layer supports querying by both `payload.topic_id` and `payload.partial_attributes.topic_id`

#### Concurrent Update Protection

* Added `update_fields()` method to LectureRepository for partial updates
* Prevents race conditions when audio and summary generation run in parallel
* Each job only updates its specific fields without overwriting others

## Async Generation Jobs

* generate_course
* generate_department
* generate_lecture
* generate_lecture_audio
* generate_lecture_summary
* generate_professor
* generate_professor_image
* generate_topics_for_course
