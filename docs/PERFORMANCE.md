# Performance and Concurrency Guide (Alpha)

This project now offloads blocking work to threads to keep the FastAPI event loop responsive while jobs run in the background.

## What we changed (server)

- Moved blocking calls to threads using `asyncio.to_thread`:
  - S3/MinIO operations in `artificial_u/services/storage_service.py`
  - ElevenLabs TTS work during audio generation in `artificial_u/services/lecture_generator_service.py`
  - Job repository calls inside the worker loop in `artificial_u/api/worker.py`

These changes prevent slow jobs (e.g., generate lecture/audio) from blocking request handling and SSE streaming.

## Tuning knobs

- `WORKER_MAX_CONCURRENCY` (default 2–3): how many jobs run concurrently in a single process. Raise gradually.
- `OUTBOUND_RPS`: global rate limit for external providers; keep conservative to avoid throttling.
- Thread pool size (optional):
  - In app startup you can increase the default executor size if you run many blocking operations:
    - `asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=8))`

## Alpha deployment (Gunicorn + Uvicorn workers)

Run multiple app processes to isolate heavy jobs from routine traffic:

```bash
gunicorn -k uvicorn.workers.UvicornWorker artificial_u.api.app:app \
  --workers 2 \
  --threads 8 \
  --timeout 120
```

- Start with 2 workers on small instances; scale to 3–4 as needed.
- The `--threads` pool is used by Uvicorn for request handling; our blocking work runs in the Python default executor created per process.

## SSE and client considerations

- Keep a single `EventSource` per page; share it across components to avoid redundant connections.
- Heartbeats are already emitted (`event: ping`) to keep intermediaries happy.
- For simple “done/failed” status, polling every 2s works well and reduces open sockets.

## Observability checklist

- Log job lifecycle: reserved → running → done/failed; verify smooth progression under concurrency.
- Track HTTP latency during long-running jobs; target sub‑500ms for routine endpoints.
- Watch provider error rates when increasing `OUTBOUND_RPS`.

## When to consider bigger moves

- External queue/worker (Redis + RQ/Celery) if you need cross‑process job distribution, autoscaling, or long‑lived workers independent of the API.
- Async stacks (SQLAlchemy async, aioboto3) for fewer threads and improved efficiency once the architecture stabilizes.
- WebSockets for richer, bi‑directional progress updates; SSE + polling is sufficient for alpha.

## Quick validation locally

1) Start a long `generate_lecture_audio` job.
2) Browse several pages; responses should remain fast while jobs run.
3) Enqueue multiple jobs; verify they process concurrently without starving HTTP.
