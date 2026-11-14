# Refactor Notes

Follow-ups from the November 2026 cleanup (branch `cleanup/dead-code-and-dry`). The first pass
removed the CLI, the Ollama leftovers, about twenty unused endpoints and a lot of dead code. A
second pass worked through this list and fixed everything that did not need a product or
operations decision. What remains is below. Items marked *unverified* come from reading the code
only.

## TODO: lecture generation should use the lecture model if set

Applies to both paths:

- **Batch:** `POST /topics/{id}/generate-remaining-lectures` and
  `/regenerate-remaining-lectures` (`_enqueue_lecture_chain` in
  `artificial_u/api/routers/topics.py`), chained by the worker's follow-up logic.
- **Single:** `POST /lectures/generate/enqueue` and `/lectures/generate/text-only/enqueue` in
  `artificial_u/api/routers/lectures.py`.

How the model is chosen today (`PreferenceService.get_lecture_generation_model`, called from
`LectureGeneratorService.generate_lecture`):

1. the course's `settings.lecture_generation_model`
2. the requesting student's `LECTURE_GENERATION_MODEL` preference
3. the global preference
4. the `LECTURE_GENERATION_MODEL` setting

Things to check or change:

- Step 2 is effectively dead. Nothing in the code can write a per-student preference (only
  `PreferenceRepository.set_global` exists), so it only applies to rows inserted by hand. Either
  add a way to set it or drop the step.
- Batch jobs now carry the creator's student ID (`partial_attributes.created_by`), the same as
  single jobs. `tests/api/test_topic_batches.py` covers the payload. No test runs a job end to
  end and asserts which model was used.
- The jobs list reports a model per job (`_job_model_name` in `artificial_u/api/routers/jobs.py`)
  using course setting, then the global preference, then the setting. It never consults a
  student preference, so if step 2 is kept the label can differ from the model that ran.
- `_job_model_name` also shows `payload.model_name_override` for any job kind, but
  `_handle_generate_lecture` in `artificial_u/services/job_service.py` never reads that key. A
  per-job lecture model would have to be threaded through there.

## Needs a decision

These were left alone because the right change depends on what you want.

### Failure handling

- **API services returning `None` on database errors**, which routers report as 404, and
  `integrations/elevenlabs/client.py` turning any API error into `None` or an empty list. Fixing
  either changes status codes and what callers see during an outage. See "Domain exception
  handlers" below.
- **`models/engine.py`** returns the first engine created regardless of the `db_url` passed
  later. Raise, warn, or key the engine by URL?

### Operations

- **Remaining `async def` routes that never `await`.** `routers/voices.py` and
  `routers/quickstart.py` are converted to plain `def`, and FastAPI's threadpool is capped by
  `API_THREADPOOL_SIZE` (12): below the 15-connection pool, leaving 3 connections for the job
  worker. About 50 handlers in the other routers still run synchronous database calls on the
  event loop. They are short, so the benefit is smaller, but the same change applies. If
  `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` or `WORKER_MAX_CONCURRENCY` change, keep
  `API_THREADPOOL_SIZE` at or below pool minus worker concurrency.
- **xAI TTS language.** The xAI backend detects the language from the text
  (`XAI_TTS_LANGUAGE=auto`); no caller passes the lecture's language. Passing it would be
  explicit but would override the setting.
- **`scripts/create_fts_index.py`** creates an index no query uses, and nothing calls the script
  any more; *unverified* whether production has the index. The backfill scripts wired into
  `scripts/docker-entrypoint.sh` are being kept for now.
- **CI rewrites `.env.test`.** `test.yml` and `test-quick.yml` overwrite the committed file with
  heredocs. Dropping them would leave one source of truth, but they add storage and Auth0 values
  the committed file lacks.

### Housekeeping

- **Endpoints with no frontend caller that were kept:** `POST /courses` and
  `POST /tags/backfill/enqueue`.
- **Repository methods used only by tests:** `LectureRepository.get_content`, `get_audio_url`,
  `get_transcript_url`, and `TopicRepository.create_batch`, `list_by_course_week`. Removing them
  means editing the broader integration tests that call them.

## Optional refactors still open

No decision needed; these are larger or lower-value than what was done.

### API layer

- **Domain exception handlers.** Registering handlers for `*NotFoundError` and `DatabaseError`
  would let services raise, removing about 40 try/except blocks and the "re-query to tell 404
  from 500" code in the routers. Changes failure-path status codes.
- **`get_or_404` with ownership check.** The "fetch, 404, `verify_asset_ownership`" block appears
  at about 20 sites. The 404 messages differ slightly between them.
- **Unreachable branches.** Router checks for a `None` the service never returns
  (`routers/courses.py`, `routers/lectures.py`). The mocked API tests encode the `None` contract
  and would need to raise 404 instead.
- **Pagination.** Eight list models repeat `items/total/page/size/pages`; a generic `Page[T]`
  would replace them but renames OpenAPI schemas. `StudentBrief` is defined four times.
- **Worker payload builders.** `_build_audio_payload` and `_build_timeline_payload`, and
  `_handle_timeout` and `_handle_exception`, in `api/worker.py` are near-duplicates.
- **Service wiring.** `api/dependencies.py` still calls some dependency functions directly, and
  the API services build their own core and generator services, so several objects are
  constructed more than once per request.
- **Environment variables read outside `Settings`** in `api/worker.py`, `api/app.py`,
  `api/utils/logging.py`, `api/tracemalloc_diag.py` and `api/cloudwatch_metrics.py`.

### Services

- **Lecture slide images** still carry their own copy of the fallback ladder in
  `ImageService.generate_lecture_slide_image` (it differs in reference-image handling).
- **Lecture and topic-list XML extraction** still have their own sequences with truncation
  recovery; the other generators now share `extract_root_xml`.
- **`ContentService` provider branches** repeat the token and temperature defaults and the
  "log, store content log, return" tail four times. The unit tests call the provider methods
  directly, so changing their return shape means rewriting those tests.
- **Lecture asset cleanup** is written four times, and the `course_code / week / order` storage
  key parts are derived six times with slightly different fallbacks.
- **Not-found checks after get-or-raise calls** in the generator services cannot fire, and
  `TopicService.get_topic` returns `None` where its siblings raise.

### Models, integrations and prompts

- **TTS clients.** The Mistral, xAI, Qwen and ElevenLabs clients each have their own retry loop
  and "audio unexpectedly small" warning, and API keys are resolved at three layers.
- **French prompt modules** duplicate the English builder functions; only the strings differ.
- **`models/converters.py`** has six identical `model_dump` wrappers and five "field or marker"
  loops with subtly different emptiness tests.

## Resolved in the second pass

Kept for reference; see the git history for details.

- **Bugs:** the image model recorded for professors and courses is now the one that produced the
  image; deleting a topic removes every lecture revision; `JsonFormatter` emits `extra=` fields;
  French professor and department prompts use the `[GENERATE]` placeholder the parser knows; the
  course language reaches generated departments and professors; a failed revision lookup no
  longer produces a second "revision 1"; model refusals keep their message in job errors; eight
  professor routes no longer expose a stray `logger` query parameter; the wildcard CORS origin
  matches subdomains.
- **Security and tooling:** `/share/og-image` only reads our images bucket and our public site;
  `.dockerignore` keeps tests, the frontend and `.env.*` out of the image; CI runs on changes to
  tests, scripts and migrations; test mode is no longer guessed from `sys.argv`;
  `scripts/setup_test_db.py` refuses databases not named `*_test`; provider clients no longer
  detect pytest or import `MagicMock`.
- **CloudFront:** the distribution-wide error responses that turned every 403 and 404
  (including those from `/api/*`) into `200` + `index.html` are replaced by a CloudFront
  Function that serves `index.html` for SPA routes on the frontend behavior only. Takes
  effect on the next `cdk deploy`. SPA routes must not end in a segment containing a dot.
- **Decisions applied:** the voice endpoints that change a professor's voice or make paid
  provider calls are limited to the professor's creator and admins (admin-only when the
  professor has no recorded creator, or a preview names no professor); cancelling a job is
  limited to admins and the student recorded in the job's payload; replacing a topic that already has a lecture is refused; lecture generation
  fails when the professor, earlier lectures or topic list cannot be loaded; a course-creation
  job whose topics cannot be saved fails once, without retry (`NonRetryableJobError`);
  `scripts/rebuild_dev_db.py` no longer touches migration files and refuses non-local databases;
  `AGENTS.md` and `.github/copilot-instructions.md` are generated copies of `CLAUDE.md`.
- **Refactors:** one fallback ladder for course and professor images; `extract_root_xml` in four
  generators; one decision step for the three selector services
  (`artificial_u/services/selection.py`); one implementation for the batch lecture endpoints;
  shared query helpers and an eager-loaded creator in `LectureRepository`; `model_validate` for
  student and preference responses; one professor review response in the quickstart router;
  function-local imports hoisted across `api/` and `services/`; router-wide service construction
  removed from the lectures and departments routers.

## mypy status

mypy is not run in CI. `uv run mypy artificial_u` reports 485 errors, down from 710 on `main`
before the cleanup; the drop came from deleting and consolidating code, not from fixing types.

Most of the errors are `arg-type` and `assignment`, about half are in
`artificial_u/models/repositories/`, and about half mention `Column[...]`. They come from the
SQLAlchemy models in `models/database.py` using untyped `Column(...)` declarations, so every
attribute read or write looks like a `Column` to mypy. Moving the models to `Mapped[...]` /
`mapped_column` would clear most of them in one change.
