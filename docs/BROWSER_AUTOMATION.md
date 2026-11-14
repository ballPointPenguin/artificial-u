# Browser Automation

How a coding agent (or you) drives the web app in a real browser: to check a change, look into
a bug, or review a page. It uses the [Playwright CLI](https://github.com/microsoft/playwright-cli)
with dedicated low-privilege accounts, so browsing cannot run up provider bills by accident.

The same engine runs a small suite of read-only smoke tests; see [Smoke tests](#smoke-tests).

## Setup

```bash
npm install -g @playwright/cli@latest   # Node 20+
playwright-cli install --skills         # refreshes .claude/skills/playwright-cli
```

The CLI uses your installed Chrome. Then put the account settings in
`.playwright/auth/accounts.env`, or in your `.env` (both gitignored; `.env.example` has the
lines commented out). The first file wins if both exist.

```bash
AGENT_PASSWORD='...'
AGENT_LOCAL_CREATOR=agent@artificial-u.com
AGENT_LOCAL_VIEWER=agent-viewer@artificial-u.com
AGENT_PROD_CREATOR=agent2@artificial-u.com
AGENT_PROD_VIEWER=agent2-viewer@artificial-u.com
```

## Accounts

The accounts exist in Auth0. Their role and coin balance live in the app's `students` table and
are changed by an admin under Users in the web app.

| Session | Site | Role | Use for |
|---------|------|------|---------|
| `local-viewer` | http://localhost:5173 | viewer | Default for looking at the local app |
| `local-creator` | http://localhost:5173 | creator | Creating or editing things locally, when asked |
| `prod-viewer` | https://artificial-u.com | viewer | Default for looking at production |
| `prod-creator` | https://artificial-u.com | creator | Creating or editing production assets, when asked |

Local accounts need the local stack running (`docker compose up -d`, `make run-api`,
`cd web && pnpm dev`).

## Opening a session

```bash
scripts/agent-browser.sh local-viewer            # prints the account, role and coin balance
scripts/agent-browser.sh local-creator --headed  # show the browser window
scripts/agent-browser.sh prod-creator --read-only
```

The script starts a browser session named after the account, signs in through Auth0 if the
session is not already signed in, and keeps a persistent profile so the login survives
restarts. After that, drive the session with `playwright-cli -s=<session> ...`:

```bash
playwright-cli -s=local-viewer goto http://localhost:5173/courses
playwright-cli -s=local-viewer snapshot          # accessibility tree with element refs
playwright-cli -s=local-viewer find "Published"  # search the snapshot
playwright-cli -s=local-viewer click f1e15       # click by ref
playwright-cli -s=local-viewer screenshot
playwright-cli -s=local-viewer console error
playwright-cli -s=local-viewer requests          # network log
playwright-cli -s=local-viewer close
```

Snapshots, screenshots and logs are written to `.playwright-cli/` (gitignored). The full command
reference is in `.claude/skills/playwright-cli/SKILL.md`.

## What stops paid calls

Generation in this app calls paid providers (LLMs, image models, text-to-speech). Three things
keep a browser session from triggering them unintentionally, strongest first:

1. **The account's role, enforced by the API.** Every route that creates, changes or generates
   something requires the creator or admin role, except editing your own profile. A viewer
   session gets a 403 before any provider is called. This holds on production and locally.
2. **The coin balance.** Creator accounts spend coins on lecture text, audio, topics and
   images, so the balance caps those. It does not cap everything: professor, department and
   summary generation cost 0 coins, and voice previews and quickstart intro audio are not
   coin-gated.
3. **`--read-only`.** The browser answers every non-GET API request with a 403 itself. Useful
   with a creator session when you only want to look. It is a convenience inside one browser
   session, not a security boundary.

Never sign these sessions in with an admin account: admins bypass coin checks entirely.

## Rules for agents

- Use a viewer session unless the task needs to create or change something.
- With a creator session, do not start generation (anything labelled generate, regenerate,
  create with AI, voice preview, quickstart) unless the user asked for that specific action in
  this conversation. One explicit request covers one action, not a loop.
- On production, creating, editing or deleting anything needs an explicit request each time.
- Do not paste credentials, tokens or the contents of `.playwright/auth/` into chat, commits,
  issues or logs.
- Close sessions when done (`playwright-cli close-all`).

## Smoke tests

`web/e2e/` holds Playwright tests that walk the public pages as an anonymous visitor: home,
browse, the course catalogue and a course, a lecture with audio playback, search, departments,
the login prompt on protected pages, the static pages, and two API checks.

```bash
cd web
pnpm exec playwright install chromium                 # once
pnpm test:e2e                                         # local stack; API and `pnpm dev` running
E2E_BASE_URL=https://artificial-u.com pnpm test:e2e   # production
pnpm test:e2e:report                                  # open the HTML report of the last run
```

They are safe to run anywhere. There is no login, and a fixture in `e2e/fixtures.ts` refuses
every non-GET API request inside the browser and fails the test that made it. They assume only
that at least one published course exists; the lecture test finds a lecture with audio through
the API and skips if there is none.

Not covered yet: anything behind a login, and create/edit/generate flows. Those need recorded
provider responses so they can run without paid calls.

## Troubleshooting

- **"Login did not produce a session"**: check the password in `accounts.env`, and that the
  site is up. Run with `--headed` to watch the sign-in.
- **Wrong role or no coins**: change them as an admin under Users, then rerun the script.
- **Stale or confused session**: `playwright-cli -s=<session> close`, then
  `playwright-cli -s=<session> delete-data`, and run the script again.
- **Browser left running**: `playwright-cli list`, `playwright-cli close-all`, or
  `playwright-cli kill-all` for stuck processes.
