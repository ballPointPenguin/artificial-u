---
name: update-deps
description: Routine dependency maintenance for ArtificialU — upgrade Python deps (pyproject.toml, uv.lock, cdk/requirements*.txt, .pre-commit-config.yaml) and web deps (web/package.json via pnpm, web/biome.json schema), review breaking changes, then re-run pre-commit and pnpm checks. Use when asked to update, upgrade, or bump dependencies/libraries/packages.
argument-hint: "[python|web|all]"
disable-model-invocation: true
---

# Update dependencies

Scope: `$ARGUMENTS` (`python`, `web`, or `all`; default `all`).

Work on a branch (`chore/deps-YYYY-MM-DD`), never directly on `main`. Do not commit or push
unless the user asks. Keep a running list of every bump (old → new) and flag major-version
jumps — you'll need it for the breaking-change review and the final report.

## 1. Python

1. **See what's outdated:** `uv tree --outdated --depth 1`
2. **Upgrade the lockfile:** `uv lock --upgrade`, then `uv sync`.
3. **Raise floors in `pyproject.toml`:** for each package in `[project].dependencies` and
   `[dependency-groups]` (`dev`, `test`), set the `>=` floor to the version now in `uv.lock`
   (check with `uv tree --depth 1`). Keep extras (e.g. `uvicorn[standard]`) and the
   alphabetical order. Run `uv lock` again afterwards so the lock reflects the new floors.
4. **CDK requirements** (`cdk/requirements.txt`, `cdk/requirements-dev.txt`):
   - `aws-cdk-lib` is pinned with `==`. Bump it to the latest release
     (`curl -s https://pypi.org/pypi/aws-cdk-lib/json | jq -r .info.version`), and keep the
     `aws-cdk-lib` floor in the `pyproject.toml` dev group compatible.
   - Leave `constructs` within `<11.0.0` unless the latest aws-cdk-lib requires otherwise.
   - Bump the `pytest` floor in `requirements-dev.txt` to match the one in `pyproject.toml`.
5. **Pre-commit hooks:** `uv run pre-commit autoupdate`. Then check that the hook `rev`s for
   `black`, `isort`, and `flake8` match the versions locked in `uv.lock`. If they differ,
   make them match, so pre-commit and `make lint` don't disagree on formatting. Ruff is only
   in pre-commit; keep the `py314` target comment accurate.

## 2. Web (run from `web/`)

1. **See what's outdated:** `pnpm outdated`
2. **Upgrade:** `pnpm update --latest`. If a major bump looks risky (framework, router,
   Kobalte, Tailwind, Vite, ESLint), say so and ask before keeping it.
3. **Biome schema:** run `pnpm exec biome migrate --write`. It updates `biome.json`'s
   `$schema` to the installed version and migrates config keys. Confirm that `$schema`
   matches `pnpm exec biome --version`.
4. **Overrides:** check whether the `overrides` in `pnpm-workspace.yaml` are still needed
   (e.g. whether `@typescript-eslint/*` has caught up). If they are, bump them to match the
   versions now installed. Add any new packages that need build scripts to `allowBuilds`.
5. **pnpm version:** if pnpm itself was upgraded, update all three places together:
   `packageManager` in `package.json`, `pnpm` in `/mise.toml`, and `version:` for
   `pnpm/action-setup` in `.github/workflows/web-quality.yml` and `deploy.yml`.

## 3. Breaking-change review

For every **major** bump, and for any minor bump of a 0.x package:

- Read the changelog or release notes (GitHub releases, CHANGELOG.md, migration guide). Use
  WebFetch or WebSearch; don't rely on memory.
- Grep the codebase for the APIs the notes say were changed or removed. Fix the call sites,
  or pin back and explain why.
- Pay extra attention to the AI/TTS SDKs (`anthropic`, `openai`, `google-genai`,
  `elevenlabs`, `mistralai`, `dashscope`), `fastapi`, `pydantic`, `sqlalchemy`, `alembic`,
  and on the web side `solid-js`, `@solidjs/router`, `@kobalte/core`, `tailwindcss`, `vite`,
  `eslint`, `typescript`.

## 4. Validate

Run these from the repo root and fix anything that fails. Don't paper over failures.

The integration tests need the local Postgres from Docker. Make sure it's running
(`docker compose ps`; start it with `docker compose up -d`, and run
`uv run python scripts/setup_test_db.py` if the test DB doesn't exist yet). Don't skip the
integration tests: driver and ORM upgrades (e.g. SQLAlchemy 2.1 switching to psycopg 3) only
show up against a real database.

```bash
make pre-commit              # all hooks, all files; re-run if hooks rewrote files
make lint                    # black --check, isort --check-only, flake8
uv run mypy artificial_u     # not enforced in CI; compare against main, flag only new errors
uv run pytest                # unit + integration (needs the Docker DB)
```

For web changes:

```bash
cd web && pnpm lint && pnpm lint:css && pnpm exec biome ci . && pnpm test && pnpm build
```

If formatter upgrades (black, biome) reformat a lot of files, keep that in a separate commit
from the dependency bumps so the review stays readable.

## 5. Report

End with:
- A table of bumps (package, old → new, major? y/n)
- Breaking changes found and how each was handled
- Validation results, with any remaining failures quoted
- Follow-ups you skipped (risky majors you held back, overrides still needed)
