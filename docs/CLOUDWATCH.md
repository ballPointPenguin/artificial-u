# CloudWatch Observability

Recommendations for monitoring ArtificialU in AWS CloudWatch. Scoped to what
the application actually emits today plus the AWS-side signals that come for
free with the CDK stack (`cdk/cdk/cdk_stack.py`).

The deployment topology is a single ECS Fargate service (`ApiService`) running
both the FastAPI server and the background `Worker` in the same task, fronted by
an Application Load Balancer and CloudFront, backed by RDS PostgreSQL 17 and S3
buckets for media. There is no dedicated worker service yet (see
`BACKGROUND_JOBS_EVOLUTION_PLAN.md` §3.1).

---

## What's already wired up

### Custom metrics (`ArtificialU` namespace)

Emitted from [`artificial_u/api/cloudwatch_metrics.py`](../artificial_u/api/cloudwatch_metrics.py)
on a 60s loop, gated by **both** `DIAG_CLOUDWATCH_METRICS=1` **and**
`DIAG_CLOUDWATCH_METRICS_LEADER=1`. Only one Gunicorn worker per task should be
the leader, otherwise metrics double-count.

All metrics carry two dimensions:

- `Env` — from the `ENV` env var (`production`, `dev`, etc.)
- `ServiceRole` — from `SERVICE_ROLE` env var (currently always `api`; will
  diverge into `api`/`worker` once §3.1 of the evolution plan lands)

| Metric | Unit | Source | What it tells you |
|---|---|---|---|
| `jobs.queued` | Count | `JobRepository.telemetry_summary()` | Backlog depth right now |
| `jobs.running` | Count | same | In-flight jobs across all workers |
| `jobs.done` | Count | same | Lifetime completed jobs (cumulative) |
| `jobs.failed` | Count | same | Lifetime failed jobs (cumulative) |
| `jobs.cancelled` | Count | same | Lifetime cancelled jobs (cumulative) |
| `jobs.failed_last_hour` | Count | same | Rolling 1h window of failures |
| `jobs.avg_wait_seconds` | Seconds | same | Avg `now() - created_at` for queued rows |
| `sse.active_streams` | Count | `JobEventHub.subscriber_count()` | Live admin-dashboard listeners |
| `sse.publish_dropped` | Count | `JobEventHub.dropped_events_count()` | Events dropped due to full subscriber queues |
| `worker.inflight` | Count | `Worker.semaphore` | `WORKER_MAX_CONCURRENCY - available` |

Note: `jobs.done` / `jobs.failed` / `jobs.cancelled` are cumulative table
counts, not deltas. Use CloudWatch math (`RATE(m1)`) or `DIFF` to chart per-minute
throughput.

### Structured log fields (CloudWatch Logs Insights)

The worker logs every reservation/start/done/fail line through
[`_job_log_extra()`](../artificial_u/api/worker.py) with these fields:

- `job_id` (int)
- `kind` (str — e.g. `generate_lecture`, `generate_lecture_slide`, `generate_lecture_audio`)
- `attempt` (int)
- `max_attempts` (int)
- `duration_ms` (int)
- `worker_pid` (int)
- `retry_in_sec`, `next_attempt` (on retries only)

When `DIAG_PROCESS_METRICS=1`, [`artificial_u/api/telemetry.py`](../artificial_u/api/telemetry.py)
emits one log line every `DIAG_PROCESS_METRICS_INTERVAL_SEC` (default 30s) of
the form:

```
process_telemetry {"ts": "...", "pid": 7, "ppid": 1, "platform": "linux",
  "python": "3.14.x", "rss_bytes": 524288000, "vms_bytes": 1234567890,
  "num_threads": 17, "num_fds": 42, "gc_counts": [0, 0, 0],
  "sse_subscribers": 0, "worker_semaphore_available": 4,
  "worker_semaphore_in_use": 0}
```

Important: the JSON payload lives **inside** the outer log envelope's `message`
field as a string — the keys are NOT promoted to top-level Logs Insights
fields. Queries must use `parse message /.../` to extract values (see examples
below). Also note the units: `rss_bytes` and `vms_bytes` are in bytes, not
megabytes — divide by `1048576` for MB.

### IAM

The Fargate task role has `cloudwatch:PutMetricData` scoped via condition to the
`ArtificialU` namespace (see `cdk_stack.py:340-351`). Adding a new namespace
requires updating that policy.

---

## Recommended dashboards

Build one CloudWatch dashboard per concern. Pin them all in a folder so the team
hits the same view.

### 1. Job queue health (primary on-call view)

Widgets:

- **Queue depth over time** — `jobs.queued` (line, 1m period). Annotate at 10.
- **Throughput** — `RATE(jobs.done)` and `RATE(jobs.failed)` per minute (stacked area).
- **Failures last hour** — `jobs.failed_last_hour` (single value + spark line).
- **Average wait time** — `jobs.avg_wait_seconds` (line). Annotate at 60s.
- **Worker utilization** — `worker.inflight` against `WORKER_MAX_CONCURRENCY` (line + horizontal threshold).
- **Top failing kinds (last 1h)** — Logs Insights widget, query in §"Useful Logs Insights queries" below.
- **Avg duration by kind (last 1h)** — Logs Insights, same section.

### 2. Process / memory drift

Only useful while `DIAG_PROCESS_METRICS=1`.

Widgets are all Logs Insights queries (these are not CloudWatch metrics — the
fields live inside the `message` string and must be parsed out per query):

- `rss_bytes` per `pid` (one line per Gunicorn worker — watch for monotonic climb). Divide by `1048576` for MB.
- `num_fds` per `pid` (file-descriptor leaks show up here).
- `num_threads` per `pid`.
- `gc_counts` (parse the array; track gen-2 collections especially).
- `sse_subscribers` and `worker_semaphore_in_use` (sanity-check correlation with HTTP load).

If any of these graduate to first-class CloudWatch metrics later, fold them
into the Job-queue dashboard instead.

Use this to settle the open question in §5.1 of the evolution plan ("is memory
actually leaking?"). If RSS plateaus over 24h, it's steady-state heavy, not a
leak.

### 3. ECS / ALB / RDS infrastructure

Pin the AWS-managed metrics — these are emitted automatically:

- **ECS Service** (`AWS/ECS`): `CPUUtilization`, `MemoryUtilization`, `RunningTaskCount`. Filter on `ClusterName=Cluster` and `ServiceName=ApiService`.
- **ALB** (`AWS/ApplicationELB`): `RequestCount`, `TargetResponseTime` (p50/p95/p99), `HTTPCode_Target_5XX_Count`, `HTTPCode_ELB_5XX_Count`, `UnHealthyHostCount`, `RejectedConnectionCount`.
- **RDS** (`AWS/RDS`): `CPUUtilization`, `DatabaseConnections`, `FreeableMemory`, `ReadIOPS`/`WriteIOPS`, `ReadLatency`/`WriteLatency`. Filter on `DBInstanceIdentifier`.
- **S3** request metrics (opt-in per bucket; turn on for `audio-bucket` and `images-bucket` if egress costs spike): `4xxErrors`, `5xxErrors`, `BytesDownloaded`.
- **CloudFront**: `Requests`, `BytesDownloaded`, `4xxErrorRate`, `5xxErrorRate`, `OriginLatency`, `CacheHitRate`.

### 4. Container Insights

Already enabled per the evolution plan §1.6. Pin the prebuilt "Performance —
ECS" view filtered to the `Cluster` cluster. The `EphemeralStorageUtilized` and
`NetworkRxBytes`/`NetworkTxBytes` charts are useful when image jobs spike.

---

## Recommended alarms

Tier alarms by audience. CloudWatch supports composite alarms — use them to
suppress noise during deploys. Alarms here align with the evolution plan §1.4.

### Paging (real impact)

| Alarm | Threshold | Period / EvalPeriods | Notes |
|---|---|---|---|
| ALB 5xx surge | `HTTPCode_Target_5XX_Count > 5` | 1m / 3 | Treat any sustained 5xx as urgent — single Fargate task. |
| ECS service down | `RunningTaskCount < 1` | 1m / 2 | Health-check or OOM. |
| RDS CPU saturation | `CPUUtilization > 85%` | 5m / 3 | `db.t4g.small` has burst credits — also alarm on `CPUSurplusCreditsCharged > 0`. |
| RDS connections near cap | `DatabaseConnections > 90` | 1m / 5 | `t4g.small` ~110 max; pool config in `cdk_stack.py:258-262`. |
| Memory at OOM risk | ECS `MemoryUtilization > 85%` | 5m / 3 | Below the 90% kill line; gives time to react. |

### Warning (inspect within hours)

| Alarm | Threshold | Why |
|---|---|---|
| Backlog building | `jobs.queued > 10` | 15m sustained | Per evolution plan §1.4. |
| Failure spike | `jobs.failed_last_hour > 3` | 5m / 1 | Detects model/provider regressions early. |
| Wait time | `jobs.avg_wait_seconds > 120` | 10m / 2 | Workers can't keep up. |
| Stuck jobs | derived metric: `jobs.running` flat & non-zero for 30m+ | composite | Visibility-timeout / heartbeat issue. |
| SSE drops | `sse.publish_dropped > 0` | 5m / 1 | Slow consumers; subscribers missing events. |
| ALB 4xx spike | `HTTPCode_Target_4XX_Count > N` | 5m / 3 | Auth/validation regression after a deploy. |
| Memory creep | `MemoryUtilization > 80%` | 5m / 3 | Per evolution plan §1.4. |
| RDS storage | `FreeStorageSpace < 5GB` | 15m / 1 | 20GB allocated; grow or prune. |
| RDS replica lag | only relevant if a read replica is added later | — | — |

### Informational (dashboard-only, no notification)

- `worker.inflight` consistently at `WORKER_MAX_CONCURRENCY` for >30m → time to scale workers.
- `sse.active_streams` outside expected band (e.g., >50 or stuck at 0 with traffic).
- CloudFront `5xxErrorRate > 1%` for 15m.

### Suppression patterns

Wrap `jobs.queued` and `jobs.failed_last_hour` alarms in a **composite alarm**
that's gated off during deploys (correlate with ECS `DeploymentRollbackInitiated`
or simply with task-count fluctuations). This prevents noisy pages every release.

---

## Useful Logs Insights queries

Log group: `/aws/ecs/...` (default Fargate log driver writes here; check the
service's log configuration if you've customized).

### Failures by kind, last hour

```
fields @timestamp, kind, job_id, attempt, max_attempts, @message
| filter @message like /Job .* failed/
| stats count() as failures by kind
| sort failures desc
| limit 20
```

### Avg duration by kind

```
fields @timestamp, kind, duration_ms
| filter ispresent(duration_ms) and @message like /Job done/
| stats avg(duration_ms) as avg_ms, pct(duration_ms, 95) as p95_ms, count() as n by kind
| sort avg_ms desc
```

### Per-worker memory drift (when `DIAG_PROCESS_METRICS=1`)

The telemetry payload is embedded as JSON inside `message` ("process_telemetry
{...}"), so values must be parsed out with regex. Bytes are converted to MB in
the projection.

```
filter logger = "artificial_u.api.telemetry" and message like /process_telemetry/
| parse message /"pid":\s*(?<pid>\d+)/
| parse message /"rss_bytes":\s*(?<rss_bytes>\d+)/
| parse message /"num_fds":\s*(?<num_fds>\d+)/
| parse message /"num_threads":\s*(?<num_threads>\d+)/
| parse message /"sse_subscribers":\s*(?<sse_subscribers>\d+)/
| parse message /"worker_semaphore_in_use":\s*(?<worker_inflight>\d+)/
| stats max(rss_bytes / 1048576) as peak_rss_mb,
        max(num_fds) as peak_fds,
        max(num_threads) as peak_threads,
        max(worker_inflight) as peak_inflight
        by bin(5m), pid
| sort @timestamp asc
```

For a single-pid trend chart, drop the `pid` group-by and add
`filter pid = "7"` (or whichever PID).

### Retry storms

```
fields @timestamp, kind, job_id, attempt, retry_in_sec
| filter ispresent(retry_in_sec)
| stats count() as retries by kind, bin(5m)
| sort @timestamp desc
```

### Slowest jobs in window

```
fields @timestamp, kind, job_id, duration_ms
| filter ispresent(duration_ms) and duration_ms > 30000
| sort duration_ms desc
| limit 50
```

### Stuck-job sweeps

```
fields @timestamp, @message
| filter @message like /Swept .* stuck jobs/
| sort @timestamp desc
```

A frequent occurrence here points at the visibility-timeout / execution-timeout
mismatch noted in evolution plan §2.1.

---

## Filter / dimension cheatsheet

When charting custom metrics in the console:

- Always pin both dimensions (`Env` and `ServiceRole`) — leaving them off
  aggregates across environments and gives misleading totals.
- For per-host process metrics, group by `pid` in Logs Insights, not in metrics
  (the `pid` is in the JSON payload, not a metric dimension).

For Logs Insights:

- Filter by `kind` first when a specific job type is suspect — that's the
  highest-cardinality useful field.
- Use `bin(5m)` over `bin(1m)` for anything past the last hour (faster and
  cheaper to scan).
- Saved queries: park the queries above under "Saved queries" in the Logs
  Insights UI so the team doesn't re-derive them under pressure.

---

## Rolling out alarms / metrics

1. **Enable emission** on production by setting these in the CDK env block
   (currently `"0"` in `cdk_stack.py:222-230`):

   ```python
   "DIAG_CLOUDWATCH_METRICS": "1",
   "DIAG_CLOUDWATCH_METRICS_LEADER": "1",  # only on one task
   ```

   Today there's a single ECS task, so leader gating is implicit. Once a
   dedicated worker service exists (§3.1), set leader on exactly one of the two
   services or the metrics will double.

2. **Verify** by hitting the CloudWatch console → Metrics → Custom namespaces →
   `ArtificialU` and confirming all 10 metrics appear with the `Env=production`
   and `ServiceRole=api` dimensions.

3. **Build dashboards first**, then alarms, then notifications. Alarms without
   a dashboard for triage just generate frustrated wake-ups.

4. **Add an SNS topic** + email/Slack subscription for the paging tier. Keep a
   separate topic for warning-tier alarms so the two channels don't blend.

5. Revisit thresholds after the first week of production data — the §1.4
   numbers (`jobs.queued > 10`, `jobs.failed_last_hour > 3`) are reasonable
   defaults but should be tuned to actual traffic.

---

## Cost notes

- **Custom metrics**: 10 metrics × 2 dimensions = 10 unique metric streams. At
  $0.30/metric/month that's ~$3/mo. Negligible.
- **PutMetricData calls**: 60s interval × 10 metrics, batched 20-per-call →
  roughly 1 call/min → ~43k/month. Within the 1M free tier.
- **Logs Insights**: charged per GB scanned. The expensive habit is running
  open-ended `fields @message` over a wide time range — always scope with
  `filter` and `bin()`.
- **Container Insights**: ~$2/mo per task at this scale. Worth it.
- **ALB access logs** (if enabled): land in S3 — apply a lifecycle rule (30–90d
  expiry) or they accumulate quietly.

---

## What's intentionally not monitored yet

These are deferred until the corresponding evolution-plan items land. Listing
them so the gap is explicit:

- **Per-provider rate-limit hits** (Gemini / Anthropic / ElevenLabs / OpenAI 429s).
  See §5.4. Useful once outbound limiters are split per provider.
- **Per-batch progress** (slide jobs done / total). See §5.5 / §2.2. Today
  surfaced via `payload.batch_id` queries in the DB; not yet a metric.
- **Workflow / follow-up chain depth**. Logged but not aggregated.
- **Queue-depth-based autoscaling targets**. See §4.1; needs a dedicated worker
  service first.
- **Per-kind queue depth**. `jobs.queued` is currently global. If image-batch
  load swamps interactive jobs (despite priority lanes from §2.7), split this
  metric by `kind`.
