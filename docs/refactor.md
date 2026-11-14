# Refactor Notes

Follow-ups from the November 2026 cleanup pass (branch `cleanup/dead-code-and-dry`), which removed
the CLI, the Ollama leftovers, about twenty unused endpoints and a lot of dead code. Everything
here was found during that pass and deliberately left alone. Items marked *unverified* come from
reading the code only; nothing was run to confirm them.

## TODO: lecture generation should use the lecture model if set

Applies to both paths:

- **Batch:** `POST /topics/{id}/generate-remaining-lectures` and
  `/regenerate-remaining-lectures` in `artificial_u/api/routers/topics.py`, chained by the
  worker's follow-up logic in `artificial_u/api/worker.py`.
- **Single:** `POST /lectures/generate/enqueue` and `/lectures/generate/text-only/enqueue` in
  `artificial_u/api/routers/lectures.py`.

How the model is chosen today (`PreferenceService.get_lecture_generation_model`, called from
`LectureGeneratorService.generate_lecture`):

1. the course's `settings.lecture_generation_model`
2. the requesting student's `LECTURE_GENERATION_MODEL` preference
3. the global preference
4. the `LECTURE_GENERATION_MODEL` setting

Things to check or change:

- Batch jobs only started carrying the creator's student ID (`partial_attributes.created_by`) in
  the cleanup. Before that, step 2 never applied to batch generation; now it does. Decide whether
  that is wanted.
- No test runs a batch or single job end to end and asserts which model was used.
  `tests/unit/services/test_course_settings.py` covers the course setting itself.
- The jobs list reports a model per job (`_job_model_name` in `artificial_u/api/routers/jobs.py`)
  using course setting, then the *global* preference, then the setting. It skips the student
  preference, so the label can differ from the model that actually ran.
- `_job_model_name` also shows `payload.model_name_override` for any job kind, but
  `_handle_generate_lecture` in `artificial_u/services/job_service.py` never reads that key. If a
  per-job lecture model is wanted, it has to be threaded through there.

## Found but not fixed

### Bugs

- **Wrong image model recorded.** When the OpenAI fallback produces an image,
  `image_created_with` is still set from `image_service.model_name` (the Gemini default) in
  `professor_generator_service.py` and `course_generator_service.py`, and `_log_image_prompt`
  logs the default too. `ImageGenerationResult` has no model field; adding one fixes both.
- **Deleting a topic with several lecture revisions** (*unverified*). `TopicService.delete_topic`
  lists lectures through `repository.lecture.list`, which returns only the latest revision per
  topic. Older revisions stay, and deleting the topic then hits the `lectures.topic_id` foreign
  key, after the latest lecture and its files are already gone. `LectureRepository.delete_by_topic`
  exists and is only used by tests. `topic_generator_service.py` has the same exposure.
- **`JsonFormatter` drops every `extra=` field.** `artificial_u/api/utils/logging.py` reads
  `record.extra`, which never exists (logging copies the keys onto the record). The structured
  job fields the worker logs for CloudWatch Logs Insights are lost; only `request_id` survives.
- **French prompts use a different placeholder** (*effect unverified*). The templates in
  `prompts/fr/professor.py` and `prompts/fr/department.py` tell the model to fill `[GÉNÉRER]`
  fields, while the XML they embed and the parsers in `models/converters.py` use `[GENERATE]`.
- **Selectors drop the course language.** `ProfessorSelectorService` omits `language` from the
  attributes it passes to the generator, and `DepartmentSelectorService` creates departments
  without one, so a French course gets an English professor profile and department.
- **xAI TTS never receives a language.** No caller passes `language=` to
  `TTSService.synthesize_lecture_audio`.

### Security and access

- **`GET /share/og-image` fetches any URL for unauthenticated callers.** `src` is caller-supplied
  in `artificial_u/api/routers/share.py`, with no host allowlist or size cap. Only our own image
  URLs are ever passed legitimately. *Unverified* whether CloudFront or network rules limit this.
- **Missing role or ownership checks** (*intent unverified*). In `routers/voices.py`,
  `POST /voices/{professor_id}/assign_voice` changes any professor's voice, and the design,
  clone and preview endpoints trigger paid provider calls, all with only authentication.
  `routers/jobs.py` lets any authenticated user cancel any job.
- **`.dockerignore`** does not exclude `.env.test`, `tests/`, `web/` or `backups/`, so the API
  image ships them.

### Tooling hazards

- **`scripts/rebuild_dev_db.py`** (`make db-rebuild-dev`) deletes every file in
  `alembic/versions/` and autogenerates a single "Initial migration".
- **CI path filters.** `test.yml` and `test-quick.yml` only trigger on `artificial_u/**`,
  `pyproject.toml` and `uv.lock`. A PR that touches only `tests/`, `scripts/`, `alembic/` or
  `pytest.ini` runs no tests.
- **Test mode is guessed from `sys.argv`.** `config/settings.py` switches to `.env.test` when any
  argument is `-m`, `pytest` or `test`, and overwrites `os.environ` from it.
- **Production code detects pytest.** `integrations/elevenlabs/client.py` imports `MagicMock` and
  swaps it in when SDK init fails under test; the xAI and Qwen clients substitute dummy keys.
- **`models/engine.py`** returns the first engine created regardless of the `db_url` passed
  later, so a second URL in the same process is silently ignored.

### Errors that hide failures

- `job_service.py`: a failure to save pre-generated topics is logged as a warning and the job
  still succeeds, leaving a course with no topics and no fallback job.
- `lecture_generator_service.py`: `_calculate_revision_number` returns `1` on any exception, and
  database errors while loading the professor, prior lectures or topic list return empty values,
  so a lecture is generated without that context and reported as a success.
- API services in `artificial_u/api/services/` return `None` or `False` on database errors, which
  routers then report as 404.
- `integrations/elevenlabs/client.py` turns any API error into `None` or an empty list, so callers
  cannot tell an outage from "no voices".
- The CORS entry `https://*.artificial-u.com` in `config/settings.py` matches nothing, because
  Starlette's `allow_origins` is exact-match (*unverified*, from its documented behaviour).

## Optional refactors

Roughly ordered by value.

### API layer

- **Blocking work in `async def` routes.** Most route handlers never `await` and run synchronous
  SQLAlchemy or provider HTTP calls on the event loop that the in-process worker and SSE streams
  share. The worst are in `routers/voices.py` and `routers/quickstart.py` (TTS and ElevenLabs
  calls). Making the no-`await` handlers plain `def` moves them to FastAPI's threadpool; check
  the DB pool size against the threadpool first.
- **Domain exception handlers.** Registering handlers for `*NotFoundError` and `DatabaseError`
  would let services raise, removing about 40 try/except blocks and the "re-query to tell 404
  from 500" code in the routers.
- **`get_or_404` with ownership check.** The "fetch, 404, `verify_asset_ownership`" block appears
  at about 21 sites, each with a function-local import.
- **Response models built field by field.** `StudentResponse` (6 times in `routers/students.py`),
  `ProfessorDetail` plus voice-preview lookup (4 times in `routers/quickstart.py`),
  `PreferenceResponse` (3 times), and the share-page blocks in `routers/share.py`.
- **Pagination.** Eight list models repeat `items/total/page/size/pages`; a generic `Page[T]`
  would replace them. `StudentBrief` is defined four times with identical fields.
- **Near-duplicate handlers.** The batch endpoints in `routers/topics.py` and the audio/timeline
  payload builders in `api/worker.py`.
- **Service wiring.** `api/dependencies.py` calls dependency functions directly, and the API
  services build their own core and generator services, so several objects are constructed more
  than once per request. Router-level dependencies in `routers/lectures.py` and
  `routers/departments.py` build the whole graph for endpoints that never use it.
- **Unreachable branches.** Router checks for a `None` that the service can never return, and
  not-found checks after get-or-raise calls in the generator services.

### Services

- **Image generation fallback ladder** is written three times in `image_service.py`, and
  `generate_course_image` and `generate_professor_image` differ only in prompt and labels.
- **LLM response XML extraction** ("try `<output>`, else raw root, else re-wrap, else raise") is
  repeated in every generator service.
- **`ContentService` provider branches** repeat the token and temperature defaults and the
  "log, store content log, return" tail four times.
- **Lecture asset cleanup** is written four times, and the `course_code / week / order` storage
  key parts are derived six times with slightly different fallbacks.
- **`LectureGeneratorService`** builds new `StorageService` instances instead of using the one
  injected into it.
- **Selector services.** `_make_selection_decision` is the same method in the department,
  professor and course selectors apart from prompt, model and label.
- **Function-local imports.** About 60 remain across `services/` with no circular-import reason.

### Models, integrations and prompts

- **TTS clients.** The Mistral, xAI, Qwen and ElevenLabs clients each have their own retry loop
  and "audio unexpectedly small" warning, and API keys are resolved at three layers.
- **French prompt modules** duplicate the English builder functions; only the strings differ.
- **`LectureRepository`** repeats its latest-revision subquery four times, and `list()` loads
  `lecture.student` per row.
- **`models/converters.py`** has six identical `model_dump` wrappers and five "field or marker"
  loops with subtly different emptiness tests.
- **Repository methods used only by tests:** `LectureRepository.get_content`, `get_audio_url`,
  `get_transcript_url`, and `TopicRepository.create_batch`, `list_by_course_week`.

### Repo housekeeping

- **Agent instruction files.** `AGENTS.md` and `.github/copilot-instructions.md` are drifting
  copies of `CLAUDE.md`.
- **`.env.test` is loaded five ways**: a hand parser and pydantic in `config/settings.py`,
  `tests/conftest.py`, `scripts/setup_test_db.py`, and CI heredocs that overwrite the file.
- **One-off scripts still wired in.** The backfill scripts behind env flags in
  `scripts/docker-entrypoint.sh` and the "TEMPORARY" flags in `cdk/cdk/cdk_stack.py` look
  finished. `scripts/create_fts_index.py` creates an index no query uses.
- **Endpoints with no frontend caller that were kept:** `POST /courses` and
  `POST /tags/backfill/enqueue`.
- **Environment variables read outside `Settings`** in `api/worker.py`, `api/app.py`,
  `api/utils/logging.py`, `api/tracemalloc_diag.py` and `api/cloudwatch_metrics.py`.

## mypy status

mypy is not run in CI. `uv run mypy artificial_u` reports 515 errors after the cleanup, down from
710 on `main` before it; the drop came from deleting code, not from fixing types.

| Error code | Count |
|------------|-------|
| `arg-type` | 260 |
| `assignment` | 141 |
| `no-any-return` | 49 |
| everything else | 65 |

About half of the errors (261) are in `artificial_u/models/repositories/`, and 263 mention
`Column[...]`. They come from the SQLAlchemy models in `models/database.py` using untyped
`Column(...)` declarations, so every attribute read or write looks like a `Column` to mypy.
Moving the models to `Mapped[...]` / `mapped_column` would clear most of them in one change.
