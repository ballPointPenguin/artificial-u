#!/usr/bin/env bash
# Open a logged-in browser session for one of the automation accounts.
#
#   scripts/agent-browser.sh <account> [--headed] [--read-only]
#
#   --headed     show the browser window
#   --read-only  answer every non-GET request to the API with a 403 inside the browser, so
#                nothing can be created, changed or generated from this session. This is a
#                convenience, not a security boundary: the account's role is the real limit.
#
# Accounts:
#   local-viewer   read-only account on the local stack (http://localhost:5173)
#   local-creator  creator account on the local stack
#   prod-viewer    read-only account on https://artificial-u.com
#   prod-creator   creator account on https://artificial-u.com
#
# The session is named after the account and keeps a persistent browser profile, so the
# login survives between runs. Drive it afterwards with:
#
#   playwright-cli -s=<account> goto <url>
#   playwright-cli -s=<account> snapshot
#   playwright-cli -s=<account> close
#
# Credentials come from .playwright/auth/accounts.env or AGENT_* lines in .env (both
# gitignored). See docs/BROWSER_AUTOMATION.md.

set -euo pipefail

usage() {
  sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

[ $# -ge 1 ] || usage
account="$1"
shift
open_flags=()
read_only=false
for arg in "$@"; do
  case "$arg" in
    --headed) open_flags+=("--headed") ;;
    --read-only) read_only=true ;;
    *) usage ;;
  esac
done

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

# Account settings live in .playwright/auth/accounts.env, or as AGENT_* lines in .env.
# Only the AGENT_* lines are read, so the rest of .env is never evaluated by the shell.
accounts_file=".playwright/auth/accounts.env"
[ -f "$accounts_file" ] || accounts_file=".env"
if [ ! -f "$accounts_file" ] || ! grep -q '^AGENT_PASSWORD=' "$accounts_file"; then
  echo "No AGENT_* account settings found (see docs/BROWSER_AUTOMATION.md)" >&2
  exit 1
fi
set -a
eval "$(grep -E '^AGENT_[A-Z_]+=' "$accounts_file")"
set +a

case "$account" in
  local-viewer)  APP_URL="http://localhost:5173"; API_URL="http://localhost:8000/api"; EMAIL="$AGENT_LOCAL_VIEWER" ;;
  local-creator) APP_URL="http://localhost:5173"; API_URL="http://localhost:8000/api"; EMAIL="$AGENT_LOCAL_CREATOR" ;;
  prod-viewer)   APP_URL="https://artificial-u.com"; API_URL="https://artificial-u.com/api"; EMAIL="$AGENT_PROD_VIEWER" ;;
  prod-creator)  APP_URL="https://artificial-u.com"; API_URL="https://artificial-u.com/api"; EMAIL="$AGENT_PROD_CREATOR" ;;
  *) usage ;;
esac
export APP_URL API_URL EMAIL

command -v playwright-cli >/dev/null || {
  echo "playwright-cli not found: npm install -g @playwright/cli@latest" >&2
  exit 1
}

# The login steps go through a temporary file so the password never appears in a
# process argument list. Values are embedded as JSON string literals.
login_script="$(mktemp .playwright/auth/login.XXXXXX)"
trap 'rm -f "$login_script"' EXIT
node -e '
const v = (name) => JSON.stringify(process.env[name]);
process.stdout.write(`async page => {
  const appUrl = ${v("APP_URL")}, apiUrl = ${v("API_URL")};
  const email = ${v("EMAIL")}, password = ${v("AGENT_PASSWORD")};

  // Who the app thinks we are, using the access token the Auth0 SDK cached in localStorage
  const whoAmI = () => page.evaluate(async (api) => {
    const key = Object.keys(localStorage).find(
      (k) => k.startsWith("@@auth0spajs@@") && !k.includes("@@user@@"));
    const token = key && JSON.parse(localStorage.getItem(key))?.body?.access_token;
    if (!token) return null;
    const response = await fetch(api + "/v1/students/me", { headers: { Authorization: "Bearer " + token } });
    return response.ok ? response.json() : null;
  }, apiUrl);

  await page.goto(appUrl);
  await page.waitForLoadState("networkidle");
  let me = await whoAmI();

  if (!me || me.email !== email) {
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    await page.goto(appUrl + "/login");
    await page.waitForURL((url) => url.hostname.endsWith(".auth0.com"), { timeout: 30000 });
    await page.getByRole("textbox", { name: "Email address" }).fill(email);
    await page.getByRole("textbox", { name: "Password" }).fill(password);
    await page.getByRole("button", { name: "Continue", exact: true }).click();
    await page.waitForURL(
      (url) => url.origin === appUrl && !url.searchParams.has("code"), { timeout: 30000 });
    await page.waitForLoadState("networkidle");
    me = await whoAmI();
  }

  if (!me) throw new Error("Login did not produce a session for " + email);
  return { account: me.email, role: me.role, coins: me.coins, app: appUrl };
}`);
' > "$login_script"

# Reuse the session if its browser is already running, otherwise start it
if ! playwright-cli -s="$account" eval "1" >/dev/null 2>&1; then
  # ${arr[@]+...} keeps bash 3.2 (macOS) happy when the array is empty under `set -u`
  playwright-cli -s="$account" open --persistent ${open_flags[@]+"${open_flags[@]}"} >/dev/null
fi

playwright-cli -s="$account" --raw run-code --filename="$login_script"

if [ "$read_only" = true ]; then
  playwright-cli -s="$account" --raw run-code "async page => {
    await page.context().route('$API_URL/**', (route) => {
      if (route.request().method() === 'GET') return route.continue();
      return route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Blocked: this browser session is read-only' }),
      });
    });
    return 'read-only: non-GET API requests are blocked in this session';
  }"
fi
echo "Session '$account' is ready: playwright-cli -s=$account <command>"
